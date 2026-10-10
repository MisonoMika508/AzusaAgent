# -*- coding: utf-8 -*-

from pathlib import Path
import threading

from .coordinate import create_coordinate_transform
from .database import get_template, init_db, list_templates
from .settings import (
    MAX_ALIGNMENT_SHIFT_PIXELS,
    DEBUG_UI_MATCH,
    DEFAULT_GAME,
    HIGH_CONFIDENCE_THRESHOLD,
    LOW_CONFIDENCE_THRESHOLD,
)

try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None
    np = None


_cache_lock = threading.RLock()
_template_cache = {}


def _log(message):
    if DEBUG_UI_MATCH:
        print(f"[UI MATCH] {message}")


def _database_signature():
    from .settings import DATABASE_PATH

    if not DATABASE_PATH.exists():
        return (0, 0)
    stat = DATABASE_PATH.stat()
    return (stat.st_mtime_ns, stat.st_size)


def _features(gray):
    small = cv2.resize(gray, (320, 180), interpolation=cv2.INTER_AREA)
    blurred = cv2.GaussianBlur(small, (5, 5), 0)
    histogram = cv2.calcHist([blurred], [0], None, [32], [0, 256])
    cv2.normalize(histogram, histogram, alpha=1, beta=0, norm_type=cv2.NORM_L1)
    orb = cv2.ORB_create(nfeatures=600, fastThreshold=12)
    keypoints, descriptors = orb.detectAndCompute(blurred, None)
    return blurred, histogram, keypoints, descriptors


def _load_templates(game):
    init_db()
    signature = _database_signature()
    cache_key = (game, signature)

    with _cache_lock:
        cached = _template_cache.get(cache_key)
        if cached is not None:
            return cached

        templates = []
        for template in list_templates(game=game):
            image = cv2.imread(template["image_path"], cv2.IMREAD_GRAYSCALE)
            if image is None:
                _log(f"skip unreadable template={template['id']} path={template['image_path']}")
                continue

            blurred, histogram, keypoints, descriptors = _features(image)
            template["_width"] = image.shape[1]
            template["_height"] = image.shape[0]
            template["_features"] = (blurred, histogram, keypoints, descriptors)
            templates.append(template)

        _template_cache.clear()
        _template_cache[cache_key] = templates
        return templates


def _orb_similarity(template_descriptors, current_descriptors, template_keypoints, current_keypoints):
    if template_descriptors is None or current_descriptors is None:
        return 0.0
    if len(template_descriptors) < 2 or len(current_descriptors) < 2:
        return 0.0

    matcher = cv2.BFMatcher(cv2.NORM_HAMMING)
    pairs = matcher.knnMatch(template_descriptors, current_descriptors, k=2)
    good = [first for first, second in pairs if first.distance < 0.75 * second.distance]
    denominator = max(1, min(len(template_keypoints), len(current_keypoints), 60))
    return min(1.0, len(good) / denominator)


def _similarity(template_features, current_features):
    template_gray, template_hist, template_keypoints, template_desc = template_features
    current_gray, current_hist, current_keypoints, current_desc = current_features

    if template_gray.shape != current_gray.shape:
        current_gray = cv2.resize(
            current_gray,
            (template_gray.shape[1], template_gray.shape[0]),
            interpolation=cv2.INTER_AREA,
        )

    difference = cv2.absdiff(template_gray, current_gray)
    pixel_similarity = 1.0 - float(np.mean(difference)) / 255.0
    histogram_correlation = cv2.compareHist(
        template_hist,
        current_hist,
        cv2.HISTCMP_CORREL,
    )
    histogram_similarity = max(0.0, min(1.0, (histogram_correlation + 1.0) / 2.0))
    feature_similarity = _orb_similarity(
        template_desc,
        current_desc,
        template_keypoints,
        current_keypoints,
    )
    score = 0.75 * pixel_similarity + 0.10 * histogram_similarity + 0.15 * feature_similarity
    return max(0.0, min(1.0, score))


def _alignment_shift(template_features, current_features):
    template_gray = template_features[0]
    current_gray = current_features[0]
    if template_gray.shape != current_gray.shape:
        current_gray = cv2.resize(
            current_gray,
            (template_gray.shape[1], template_gray.shape[0]),
            interpolation=cv2.INTER_AREA,
        )

    shift, _response = cv2.phaseCorrelate(
        np.float32(template_gray),
        np.float32(current_gray),
    )
    return float(shift[0]), float(shift[1])


def match_screenshot(
    image_path,
    game=DEFAULT_GAME,
    mouse_size=None,
):
    """Match a screenshot against same-game templates using CPU OpenCV features."""

    if cv2 is None or np is None:
        return {
            "matched": False,
            "score": 0.0,
            "reason": "opencv_unavailable",
            "fallback": "ai_vision",
            "ui_elements": [],
        }

    image_path = Path(image_path)
    current = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if current is None:
        return {
            "matched": False,
            "score": 0.0,
            "reason": "screenshot_unreadable",
            "fallback": "ai_vision",
            "ui_elements": [],
        }

    screen_height, screen_width = current.shape[:2]
    mouse_transform = None
    if mouse_size and tuple(mouse_size) != (screen_width, screen_height):
        mouse_transform, coordinate_reason = create_coordinate_transform(
            screen_width,
            screen_height,
            int(mouse_size[0]),
            int(mouse_size[1]),
        )
        if mouse_transform is None:
            result = {
                "matched": False,
                "score": 0.0,
                "reason": f"mouse_{coordinate_reason}",
                "fallback": "ai_vision",
                "screen_size": [screen_width, screen_height],
                "mouse_size": list(mouse_size),
                "ui_elements": [],
            }
            _log(f"image={image_path} reason={result['reason']} match=FAILED -> AI fallback")
            return result

    templates = _load_templates(game)
    if not templates:
        result = {
            "matched": False,
            "score": 0.0,
            "reason": "no_templates",
            "fallback": "ai_vision",
            "game": game,
            "screen_size": [screen_width, screen_height],
            "ui_elements": [],
        }
        _log(f"image={image_path} game={game} reason=no_templates match=FAILED -> AI fallback")
        return result

    current_features = _features(current)
    best_template = None
    best_score = -1.0
    best_reason = "low_similarity"
    best_alignment_shift = (0.0, 0.0)

    for template in templates:
        transform, transform_reason = create_coordinate_transform(
            template["width"],
            template["height"],
            screen_width,
            screen_height,
        )
        if transform is None:
            if best_template is None:
                best_reason = transform_reason
            continue

        score = _similarity(template["_features"], current_features)
        alignment_shift = _alignment_shift(template["_features"], current_features)
        if score > best_score:
            best_score = score
            best_template = template
            best_reason = ""
            best_alignment_shift = alignment_shift

    if best_template is None:
        result = {
            "matched": False,
            "score": 0.0,
            "reason": best_reason,
            "fallback": "ai_vision",
            "game": game,
            "screen_size": [screen_width, screen_height],
            "ui_elements": [],
        }
        _log(f"image={image_path} reason={best_reason} match=FAILED -> AI fallback")
        return result

    transform, transform_reason = create_coordinate_transform(
        best_template["width"],
        best_template["height"],
        screen_width,
        screen_height,
    )
    enabled_elements = [
        element
        for element in best_template["ui_elements"]
        if element["enabled"]
    ]

    if best_score < LOW_CONFIDENCE_THRESHOLD:
        reason = "low_similarity"
    elif best_score < HIGH_CONFIDENCE_THRESHOLD:
        reason = "uncertain_similarity"
    elif max(abs(best_alignment_shift[0]), abs(best_alignment_shift[1])) > MAX_ALIGNMENT_SHIFT_PIXELS:
        reason = "window_offset_or_scene_shift"
    elif not enabled_elements:
        reason = "no_ui_elements"
    else:
        reason = ""

    matched = not reason
    mapped_elements = [transform.map_element(element) for element in enabled_elements] if matched else []
    if matched and mouse_transform is not None:
        mapped_elements = [mouse_transform.map_element(element) for element in mapped_elements]
    result = {
        "matched": matched,
        "score": round(best_score, 4),
        "reason": reason,
        "fallback": "" if matched else "ai_vision",
        "template_id": best_template["id"],
        "template_name": best_template["name"],
        "game": best_template["game"],
        "template_size": [best_template["width"], best_template["height"]],
        "screen_size": [screen_width, screen_height],
        "mouse_size": list(mouse_size) if mouse_size else [screen_width, screen_height],
        "alignment_shift": [round(best_alignment_shift[0], 3), round(best_alignment_shift[1], 3)],
        "scale": {
            "x": round(transform.scale_x, 6),
            "y": round(transform.scale_y, 6),
            "mouse_x": round(mouse_transform.scale_x, 6) if mouse_transform else 1.0,
            "mouse_y": round(mouse_transform.scale_y, 6) if mouse_transform else 1.0,
        },
        "ui_count": len(mapped_elements),
        "ui_elements": mapped_elements,
        "thresholds": {
            "high": HIGH_CONFIDENCE_THRESHOLD,
            "low": LOW_CONFIDENCE_THRESHOLD,
        },
    }
    _log(
        f"image={image_path} template={best_template['id']} score={best_score:.3f} "
        f"screen={screen_width}x{screen_height} "
        f"threshold={HIGH_CONFIDENCE_THRESHOLD:.2f} "
        f"match={'SUCCESS' if matched else 'FAILED -> AI fallback (' + reason + ')'}"
    )
    return result


def find_ui_element(match_result, name="", function=""):
    if not isinstance(match_result, dict) or not match_result.get("matched"):
        return {
            "found": False,
            "error": "当前截图没有高置信度数据库匹配；请回退原视觉流程。",
        }

    name_query = str(name or "").strip().casefold()
    function_query = str(function or "").strip().casefold()
    if not name_query and not function_query:
        return {"found": False, "error": "请提供 name 或 function。"}

    matches = []
    for element in match_result.get("ui_elements", []):
        name_match = name_query and name_query in element["name"].casefold()
        function_match = function_query and function_query in element["function"].casefold()
        if name_match or function_match:
            matches.append(element)

    if len(matches) != 1:
        return {
            "found": False,
            "ambiguous": len(matches) > 1,
            "matches": matches,
            "error": "没有找到唯一的已登记 UI 元素。" if not matches else "匹配到多个 UI，请用更具体的名称或功能。",
        }

    element = matches[0]
    return {
        "found": True,
        "template_id": match_result["template_id"],
        "score": match_result["score"],
        "screen_size": match_result["screen_size"],
        "mouse_size": match_result.get("mouse_size", match_result["screen_size"]),
        **element,
    }


def get_matched_ui_elements(match_result):
    if not isinstance(match_result, dict) or not match_result.get("matched"):
        return {
            "success": False,
            "error": "当前截图没有高置信度数据库匹配。",
            "ui_elements": [],
        }

    return {
        "success": True,
        "template_id": match_result["template_id"],
        "template_name": match_result["template_name"],
        "score": match_result["score"],
        "screen_size": match_result["screen_size"],
        "mouse_size": match_result.get("mouse_size", match_result["screen_size"]),
        "ui_elements": match_result["ui_elements"],
    }
