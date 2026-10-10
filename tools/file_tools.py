# -*- coding: utf-8 -*-

import os
import subprocess
import base64
import tempfile
import requests
import pyautogui
import pyperclip
from PIL import ImageChops, ImageGrab, Image, ImageStat
import time
import ctypes
from html.parser import HTMLParser
from urllib.parse import urlparse
from .comfyui_tools import (
    generate_comfyui_image,
    COMFYUI_TOOL,
)
from .browser_tools import (
    click_web_element,
    find_web_element,
    search_web,
    wait_for_webpage,
)
from ui_database.matcher import (
    find_ui_element,
    get_matched_ui_elements,
    match_screenshot,
)

# ============================================================
# 基础路径
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

# ============================================================
# Windows DPI
# ============================================================

def enable_dpi_awareness():
    """
    使用 Per-Monitor V2 DPI Awareness。
    必须在程序创建 Tkinter 窗口之前执行。
    """

    try:
        user32 = ctypes.windll.user32

        DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = -4

        result = user32.SetProcessDpiAwarenessContext(
            DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2
        )

        if result:
            print("[DPI] Per-Monitor V2 已启用")
        else:
            print("[DPI] Per-Monitor V2 设置失败")

    except Exception as e:
        print(
            "[DPI] 初始化失败："
            f"{type(e).__name__}: {e}"
        )


enable_dpi_awareness()

def get_screen_info():

    width, height = pyautogui.size()

    try:
        user32 = ctypes.windll.user32

        hdc = user32.GetDC(0)

        dpi_x = ctypes.windll.gdi32.GetDeviceCaps(
            hdc,
            88
        )

        dpi_y = ctypes.windll.gdi32.GetDeviceCaps(
            hdc,
            90
        )

        user32.ReleaseDC(0, hdc)

    except Exception:
        dpi_x = 96
        dpi_y = 96

    return {
        "width": width,
        "height": height,
        "dpi_x": dpi_x,
        "dpi_y": dpi_y,
        "scale_x": dpi_x / 96.0,
        "scale_y": dpi_y / 96.0,
    }

# ============================================================
# 工具：获取屏幕截图
# ============================================================


# ============================================================
# 工具：获取屏幕局部区域
# ============================================================

# ============================================================
# 最近一次局部截图信息
# ============================================================

_LAST_SCREEN_REGION = None

# ============================================================
# 工具：根据第一次坐标自动放大区域
# ============================================================

# ============================================================
# 工具：根据第一次坐标自动放大区域
# ============================================================

def inspect_screen_region(
    x,
    y,
    region_size=300,
    scale=3,
    refine=False
):
    """
    两级视觉搜索工具。refine=True 时，x/y 属于上一张局部图，
    并会自动映射回屏幕坐标后再截取精确区域。
    """

    global _LAST_SCREEN_REGION

    try:
        screen = ImageGrab.grab()
        screen_width, screen_height = screen.size

        x = float(x)
        y = float(y)
        region_size = int(region_size)
        scale = float(scale)
        refine = bool(refine)

        region_size = max(200, min(region_size, 1000))
        scale = max(1.0, min(scale, 4.0))

        if refine:
            if _LAST_SCREEN_REGION is None:
                return {
                    "success": False,
                    "error": (
                        "refine=True 时没有可用的上一次局部截图。"
                        "必须先进行第一次 inspect_screen_region。"
                    ),
                }

            previous = _LAST_SCREEN_REGION
            previous_scale = float(previous["scale"])
            if previous_scale <= 0:
                return {
                    "success": False,
                    "error": "上一次局部截图的 scale 无效。",
                }

            x = float(previous["origin_x"]) + x / previous_scale
            y = float(previous["origin_y"]) + y / previous_scale

        x = int(round(x))
        y = int(round(y))

        half = region_size // 2
        left = x - half
        top = y - half
        right = x + half
        bottom = y + half

        if left < 0:
            right -= left
            left = 0

        if top < 0:
            bottom -= top
            top = 0

        if right > screen_width:
            left -= right - screen_width
            right = screen_width

        if bottom > screen_height:
            top -= bottom - screen_height
            bottom = screen_height

        left = max(0, int(left))
        top = max(0, int(top))
        right = min(screen_width, int(right))
        bottom = min(screen_height, int(bottom))

        region = screen.crop(
            (
                left,
                top,
                right,
                bottom
            )
        )

        original_width = region.width
        original_height = region.height

        if scale > 1:
            try:
                resample = Image.Resampling.LANCZOS
            except AttributeError:
                resample = Image.LANCZOS

            region = region.resize(
                (
                    int(original_width * scale),
                    int(original_height * scale),
                ),
                resample,
            )

        screenshot_dir = os.path.join(
            BASE_DIR,
            "screen_cache"
        )

        os.makedirs(
            screenshot_dir,
            exist_ok=True
        )

        timestamp = time.strftime(
            "%Y%m%d_%H%M%S"
        )

        millis = int(
            (time.time() % 1) * 1000
        )

        path = os.path.join(
            screenshot_dir,
            f"region_{timestamp}_{millis:03d}.png"
        )

        region.save(
            path,
            "PNG"
        )

        _LAST_SCREEN_REGION = {
            "origin_x": left,
            "origin_y": top,
            "width": original_width,
            "height": original_height,
            "scale": scale,
            "zoomed_width": region.width,
            "zoomed_height": region.height,
        }

        print(
            "[视觉系统] "
            + ("第二级精确搜索" if refine else "第一级大范围搜索")
            + f"：origin=({left},{top}), "
            f"size=({original_width}x{original_height}), "
            f"scale={scale}, zoomed=({region.width}x{region.height})"
        )

        return {
            "success": True,
            "path": path,
            "screen_width": screen_width,
            "screen_height": screen_height,
            "origin_x": left,
            "origin_y": top,
            "region_width": original_width,
            "region_height": original_height,
            "scale": scale,
            "zoomed_width": region.width,
            "zoomed_height": region.height,
            "guess_x": x,
            "guess_y": y,
            "refine": refine,
            "message": (
                "已经获取第一级大范围视觉区域。"
                if not refine
                else "已经根据上一级视觉区域自动定位并获取第二级精确视觉区域。"
            ) + "下一步如果进行鼠标操作，请直接使用当前图片中的像素坐标，不要自行进行坐标换算。",
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"视觉区域截取失败：{type(e).__name__}: {e}",
        }

# ============================================================
# 工具：将放大截图中的坐标转换为真实屏幕坐标
# ============================================================

def resolve_zoomed_coordinate(
    x,
    y
):

    global _LAST_SCREEN_REGION

    if _LAST_SCREEN_REGION is None:

        return {
            "success": False,
            "error":
                "当前没有可用的局部放大截图。"
                "请先调用 inspect_screen_region。"
        }

    try:

        x = float(x)
        y = float(y)

    except Exception:

        return {
            "success": False,
            "error":
                "x 和 y 必须是数字。"
        }

    region_x = _LAST_SCREEN_REGION["x"]
    region_y = _LAST_SCREEN_REGION["y"]
    scale = _LAST_SCREEN_REGION["scale"]

    zoomed_width = _LAST_SCREEN_REGION[
        "zoomed_width"
    ]

    zoomed_height = _LAST_SCREEN_REGION[
        "zoomed_height"
    ]

    # --------------------------------------------------------
    # 检查坐标是否在放大图片范围内
    # --------------------------------------------------------

    if not (
        0 <= x < zoomed_width
        and
        0 <= y < zoomed_height
    ):

        return {
            "success": False,
            "error":
                f"放大图坐标超出范围："
                f"({x}, {y}) / "
                f"{zoomed_width}x{zoomed_height}"
        }

    # --------------------------------------------------------
    # 放大图坐标 → 原始局部截图坐标
    # --------------------------------------------------------

    local_x = x / scale
    local_y = y / scale

    # --------------------------------------------------------
    # 原始局部截图坐标 → 整个屏幕坐标
    # --------------------------------------------------------

    screen_x = region_x + local_x
    screen_y = region_y + local_y

    screen_x = int(round(screen_x))
    screen_y = int(round(screen_y))

    # --------------------------------------------------------
    # 最终屏幕范围检查
    # --------------------------------------------------------

    screen_width, screen_height = pyautogui.size()

    if not (
        0 <= screen_x < screen_width
        and
        0 <= screen_y < screen_height
    ):

        return {
            "success": False,
            "error":
                f"计算出的屏幕坐标超出范围："
                f"({screen_x}, {screen_y})"
        }

    return {
        "success": True,

        # DeepSeek 提供的放大图坐标
        "zoomed_x": x,
        "zoomed_y": y,

        # Python 计算出的局部原始坐标
        "local_x": round(local_x, 2),
        "local_y": round(local_y, 2),

        # 最终真实屏幕坐标
        "screen_x": screen_x,
        "screen_y": screen_y,

        # 本次截图信息
        "region_x": region_x,
        "region_y": region_y,
        "region_width":
            _LAST_SCREEN_REGION["width"],
        "region_height":
            _LAST_SCREEN_REGION["height"],
        "scale": scale,

        "message":
            f"已将放大图坐标 "
            f"({x}, {y}) "
            f"转换为真实屏幕坐标 "
            f"({screen_x}, {screen_y})。"
    }

# ============================================================
# 工具：移动鼠标
# ============================================================

def move_mouse(x, y):

    x = int(x)
    y = int(y)

    screen_width, screen_height = pyautogui.size()

    if not (
        0 <= x < screen_width
        and
        0 <= y < screen_height
    ):
        return {
            "success": False,
            "error":
                f"坐标超出屏幕范围："
                f"({x}, {y}) / "
                f"{screen_width}x{screen_height}"
        }

    pyautogui.moveTo(
        x,
        y,
        duration=0.15
    )

    return {
        "success": True,
        "x": x,
        "y": y
    }

# ============================================================
# 工具：鼠标点击
# ============================================================

def click_mouse(
    x,
    y,
    button="left"
):

    x = int(x)
    y = int(y)

    screen_width, screen_height = pyautogui.size()

    if not (
        0 <= x < screen_width
        and
        0 <= y < screen_height
    ):
        return {
            "success": False,
            "error":
                f"坐标超出屏幕范围："
                f"({x}, {y})"
        }

    if button not in (
        "left",
        "right",
        "middle"
    ):
        return {
            "success": False,
            "error":
                f"不支持的鼠标按键：{button}"
        }

    pyautogui.click(
        x=x,
        y=y,
        button=button
    )

    time.sleep(0.25)

    return {
        "success": True,
        "action": "click",
        "x": x,
        "y": y,
        "button": button
    }

# ============================================================
# 工具：按键
# ============================================================

def press_key(key):

    allowed_keys = {
        "enter",
        "esc",
        "escape",
        "tab",
        "space",
        "backspace",
        "delete",
        "up",
        "down",
        "left",
        "right",
        "home",
        "end",
        "pageup",
        "pagedown",
        "shift",
        "ctrl",
        "alt",
        "win",
        "f1",
        "f2",
        "f3",
        "f4",
        "f5",
        "f6",
        "f7",
        "f8",
        "f9",
        "f10",
        "f11",
        "f12",
    }

    key = key.lower().strip()

    if len(key) == 1:
        allowed = True
    else:
        allowed = key in allowed_keys

    if not allowed:
        return {
            "success": False,
            "error":
                f"禁止使用的按键：{key}"
        }

    pyautogui.press(key)

    time.sleep(0.15)

    return {
        "success": True,
        "action": "press_key",
        "key": key
    }

KNOWLEDGE_DIR = os.path.join(
    BASE_DIR,
    "knowledge_base"
)


# ============================================================
# 游戏路径
# ============================================================

GAME_PATHS = {
    "蔚蓝档案":
        r"C:\YostarGames\BlueArchive_JP_Gamelauncher\BlueArchive_JP_Gamelauncher.exe",
    "CS2":
        "steam://rungameid/730",
    "浏览器":
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
}


# ============================================================
# 知识文件
# ============================================================

KNOWLEDGE_FILES = {

    "总力战攻略": os.path.join(
        KNOWLEDGE_DIR,
        "总力战攻略.txt"
    ),

    "国际服千里眼": os.path.join(
        KNOWLEDGE_DIR,
        "国际服千里眼.txt"
    ),

    "国服千里眼": os.path.join(
        KNOWLEDGE_DIR,
        "国服千里眼.txt"
    ),

}


# ============================================================
# 内部：解析文件目标
# ============================================================

def _resolve_file_target(target):

    target_map = {

        "azusa_role": os.path.join(
            BASE_DIR,
            "roles",
            "Azusa.json"
        ),

        "skill": os.path.join(
            KNOWLEDGE_DIR,
            "skill.txt"
        ),

        "memory": os.path.join(
            KNOWLEDGE_DIR,
            "白洲梓_记忆.txt"
        ),

        "raid_strategy": KNOWLEDGE_FILES[
            "总力战攻略"
        ],

        "international_schedule":
            KNOWLEDGE_FILES[
                "国际服千里眼"
            ],

        "cn_schedule":
            KNOWLEDGE_FILES[
                "国服千里眼"
            ],

    }

    path = target_map.get(
        target
    )

    if path is None:
        path = target

    return os.path.abspath(path)



# ============================================================
# 工具：截图
# ============================================================

# ============================================================
# 工具：获取屏幕截图
# ============================================================

_screenshot_lock = None

try:
    import threading
    _screenshot_lock = threading.Lock()
    _screen_wait_cancel = threading.Event()
except Exception:
    _screenshot_lock = None
    _screen_wait_cancel = None


def take_screenshot():

    global _screenshot_lock

    if _screenshot_lock is not None:

        acquired = _screenshot_lock.acquire(
            timeout=3
        )

        if not acquired:

            return {
                "success": False,
                "error":
                    "截图失败："
                    "当前已有截图任务正在执行。"
            }

    try:

        screenshot_dir = os.path.join(
            BASE_DIR,
            "screen_cache"
        )

        os.makedirs(
            screenshot_dir,
            exist_ok=True
        )

        # ----------------------------------------------------
        # 每次使用唯一文件名
        # ----------------------------------------------------

        timestamp = time.strftime(
            "%Y%m%d_%H%M%S"
        )

        millis = int(
            (time.time() % 1) * 1000
        )

        screenshot_path = os.path.join(
            screenshot_dir,
            f"screen_{timestamp}_{millis:03d}.png"
        )

        last_error = None

        # ----------------------------------------------------
        # 最多重试 3 次
        # ----------------------------------------------------

        for attempt in range(3):

            image = None

            try:

                image = ImageGrab.grab()

                width, height = image.size

                image.save(
                    screenshot_path,
                    "PNG"
                )

                if not os.path.isfile(
                    screenshot_path
                ):

                    raise RuntimeError(
                        "截图文件没有生成。"
                    )

                file_size = os.path.getsize(
                    screenshot_path
                )

                if file_size <= 0:

                    raise RuntimeError(
                        "截图文件大小为 0。"
                    )

                try:
                    from ui_database.matcher import match_screenshot

                    ui_database_match = match_screenshot(
                        screenshot_path,
                        mouse_size=pyautogui.size(),
                    )
                except Exception as match_error:
                    ui_database_match = {
                        "matched": False,
                        "score": 0.0,
                        "reason": "matcher_error",
                        "fallback": "ai_vision",
                        "ui_elements": [],
                        "error": f"{type(match_error).__name__}: {match_error}",
                    }
                    print(
                        "[UI MATCH] matcher error; falling back to AI vision: "
                        f"{type(match_error).__name__}: {match_error}"
                    )

                return {
                    "success": True,
                    "path": screenshot_path,
                    "width": width,
                    "height": height,
                    "ui_database_match": ui_database_match,
                    "message":
                        "已经获取当前屏幕截图。",
                }

            except Exception as e:

                last_error = e

                time.sleep(
                    0.2
                )

            finally:

                if image is not None:

                    try:
                        image.close()
                    except Exception:
                        pass

        return {
            "success": False,
            "error":
                "截图失败，"
                "已经连续重试 3 次。"
                f"最后错误："
                f"{type(last_error).__name__}: "
                f"{last_error}",
        }

    finally:

        if _screenshot_lock is not None:

            try:
                _screenshot_lock.release()
            except Exception:
                pass


def wait_for_page_load(
    timeout=45,
    stable_seconds=2.0,
    poll_interval=0.5,
    min_wait_seconds=2.0,
):
    """Wait until the screen looks stable, then return its latest screenshot."""

    try:
        timeout = max(1.0, min(float(timeout), 120.0))
        stable_seconds = max(0.5, min(float(stable_seconds), 10.0))
        poll_interval = max(0.1, min(float(poll_interval), 2.0))
        min_wait_seconds = max(0.0, min(float(min_wait_seconds), 10.0))
    except (TypeError, ValueError) as e:
        return {
            "success": False,
            "error": f"等待参数无效：{e}",
        }

    started_at = time.monotonic()
    stable_since = None
    previous_sample = None
    latest_image = None
    visually_stable = False

    try:
        while True:
            screenshot = ImageGrab.grab()
            sample = screenshot.convert("L")
            sample.thumbnail((64, 36))

            now = time.monotonic()
            elapsed = now - started_at

            if previous_sample is not None and elapsed >= min_wait_seconds:
                difference = ImageChops.difference(
                    previous_sample,
                    sample,
                )
                average_change = ImageStat.Stat(difference).mean[0]
                difference.close()

                if average_change <= 2.0:
                    if stable_since is None:
                        stable_since = now

                    if now - stable_since >= stable_seconds:
                        visually_stable = True
                else:
                    stable_since = None

            if latest_image is not None:
                latest_image.close()

            latest_image = screenshot.copy()
            screenshot.close()

            if visually_stable or elapsed >= timeout:
                break

            if previous_sample is not None:
                previous_sample.close()

            previous_sample = sample.copy()
            sample.close()
            time.sleep(min(poll_interval, max(0.0, timeout - elapsed)))

        screenshot_dir = os.path.join(BASE_DIR, "screen_cache")
        os.makedirs(screenshot_dir, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        millis = int((time.time() % 1) * 1000)
        screenshot_path = os.path.join(
            screenshot_dir,
            f"screen_{timestamp}_{millis:03d}.png",
        )
        width, height = latest_image.size
        latest_image.save(screenshot_path, "PNG")

        elapsed = time.monotonic() - started_at
        return {
            "success": True,
            "loaded": visually_stable,
            "timed_out": not visually_stable,
            "path": screenshot_path,
            "width": width,
            "height": height,
            "elapsed_seconds": round(elapsed, 2),
            "message": (
                "屏幕画面已连续稳定，已返回最新截图。"
                if visually_stable
                else "等待超时，无法确认页面已加载完成；已返回当前截图。"
            ),
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"等待页面画面稳定失败：{type(e).__name__}: {e}",
        }
    finally:
        if previous_sample is not None:
            previous_sample.close()
        if latest_image is not None:
            latest_image.close()


def cancel_screen_wait():
    if _screen_wait_cancel is not None:
        _screen_wait_cancel.set()


def wait_for_screen_change(
    timeout=120,
    stable_seconds=0.8,
    poll_interval=0.5,
):
    """Wait for a visible screen change, then return the latest full screenshot."""

    try:
        timeout = max(1.0, min(float(timeout), 300.0))
        stable_seconds = max(0.2, min(float(stable_seconds), 5.0))
        poll_interval = max(0.1, min(float(poll_interval), 2.0))
    except (TypeError, ValueError) as e:
        return {
            "success": False,
            "error": f"等待参数无效：{e}",
        }

    if _screen_wait_cancel is not None:
        _screen_wait_cancel.clear()

    started_at = time.monotonic()
    baseline_sample = None
    previous_sample = None
    latest_image = None
    changed = False
    settled = False
    stable_since = None
    cancelled = False

    try:
        baseline = ImageGrab.grab()
        baseline_sample = baseline.convert("L")
        baseline_sample.thumbnail((64, 36))
        previous_sample = baseline_sample.copy()
        latest_image = baseline.copy()
        baseline.close()

        while time.monotonic() - started_at < timeout:
            if _screen_wait_cancel is not None and _screen_wait_cancel.is_set():
                cancelled = True
                break

            screenshot = ImageGrab.grab()
            current_sample = screenshot.convert("L")
            current_sample.thumbnail((64, 36))

            baseline_diff = ImageChops.difference(
                baseline_sample,
                current_sample,
            )
            change_score = ImageStat.Stat(baseline_diff).mean[0]
            baseline_diff.close()
            changed = changed or change_score > 1.0

            frame_diff = ImageChops.difference(
                previous_sample,
                current_sample,
            )
            frame_change = ImageStat.Stat(frame_diff).mean[0]
            frame_diff.close()

            now = time.monotonic()
            if changed and frame_change <= 1.0:
                if stable_since is None:
                    stable_since = now
            else:
                stable_since = None

            if latest_image is not None:
                latest_image.close()
            latest_image = screenshot.copy()
            screenshot.close()

            previous_sample.close()
            previous_sample = current_sample.copy()
            current_sample.close()

            if stable_since is not None and now - stable_since >= stable_seconds:
                settled = True
                break

            time.sleep(poll_interval)

        screenshot_dir = os.path.join(BASE_DIR, "screen_cache")
        os.makedirs(screenshot_dir, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        millis = int((time.time() % 1) * 1000)
        screenshot_path = os.path.join(
            screenshot_dir,
            f"screen_{timestamp}_{millis:03d}.png",
        )
        width, height = latest_image.size
        latest_image.save(screenshot_path, "PNG")

        elapsed = time.monotonic() - started_at
        return {
            "success": True,
            "changed": changed,
            "settled": settled,
            "timed_out": not settled and not cancelled,
            "cancelled": cancelled,
            "path": screenshot_path,
            "width": width,
            "height": height,
            "elapsed_seconds": round(elapsed, 2),
            "message": (
                "检测到屏幕变化并已稳定，返回最新截图。"
                if settled
                else "等待超时，画面未能稳定；返回当前截图。"
                if changed
                else "等待超时，没有检测到屏幕变化；返回当前截图。"
            ),
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"等待屏幕变化失败：{type(e).__name__}: {e}",
        }
    finally:
        for image in (baseline_sample, previous_sample, latest_image):
            if image is not None:
                image.close()

def type_text(text):
    """
    将文字复制到剪贴板并粘贴到当前焦点输入框。

    支持中文、浏览器输入框和 QQ 聊天窗口。
    """

    try:

        if not isinstance(text, str):

            return {
                "success": False,
                "error": "text 必须是字符串。"
            }

        if not text:

            return {
                "success": False,
                "error": "输入文字不能为空。"
            }

        pyperclip.copy(text)
        pyautogui.hotkey("ctrl", "v")

        return {
            "success": True,
            "message":
                "已经将文字粘贴到当前焦点输入框。"
        }

    except Exception as e:

        return {
            "success": False,
            "error":
                f"输入文字失败："
                f"{type(e).__name__}: {e}"
        }


class _WebPageTextParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title_parts = []
        self.text_parts = []
        self._in_title = False
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self._in_title = True
        if tag in {"script", "style", "noscript", "svg"}:
            self._skip_depth += 1
        if tag in {"br", "p", "div", "li", "h1", "h2", "h3", "tr"}:
            self.text_parts.append("\n")

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if tag in {"script", "style", "noscript", "svg"} and self._skip_depth:
            self._skip_depth -= 1
        if tag in {"p", "div", "li", "h1", "h2", "h3", "tr"}:
            self.text_parts.append("\n")

    def handle_data(self, data):
        if self._in_title:
            self.title_parts.append(data)
        if not self._skip_depth:
            text = data.strip()
            if text:
                self.text_parts.append(text)


def read_webpage(url, timeout=15):
    """Fetch a public webpage and return bounded HTML source plus readable text."""

    if not isinstance(url, str) or not url.strip():
        return {
            "success": False,
            "fallback_to_screenshot": True,
            "error": "必须提供网页 URL。",
        }

    url = url.strip()
    parsed_url = urlparse(url)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        return {
            "success": False,
            "fallback_to_screenshot": True,
            "error": "只支持完整的 HTTP 或 HTTPS 网页 URL。",
        }

    try:
        timeout = max(3, min(int(timeout), 30))
    except (TypeError, ValueError):
        return {
            "success": False,
            "fallback_to_screenshot": True,
            "url": url,
            "error": "timeout 必须是 3 到 30 秒之间的整数。",
        }

    try:
        response = requests.get(
            url,
            timeout=timeout,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; AzusaAgent/1.0)",
                "Accept": "text/html,application/xhtml+xml",
            },
        )
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "").lower()
        if "html" not in content_type:
            return {
                "success": False,
                "fallback_to_screenshot": True,
                "url": response.url,
                "error": f"目标不是 HTML 页面：{content_type or '未知内容类型'}。",
            }

        response.encoding = response.encoding or response.apparent_encoding
        source = response.text
        parser = _WebPageTextParser()
        parser.feed(source)
        text_content = " ".join(" ".join(parser.text_parts).split())

        if not text_content and not source.strip():
            return {
                "success": False,
                "fallback_to_screenshot": True,
                "url": response.url,
                "error": "网页没有返回可读取的 HTML 内容。",
            }

        return {
            "success": True,
            "fallback_to_screenshot": False,
            "url": response.url,
            "status_code": response.status_code,
            "title": " ".join(" ".join(parser.title_parts).split()),
            "text_content": text_content[:12000],
            "html_source_excerpt": source[:8000],
            "truncated": len(text_content) > 12000 or len(source) > 8000,
            "note": (
                "这是 HTTP 返回的源码；JavaScript 动态渲染、登录态或懒加载内容"
                "可能不在其中，必要时使用屏幕截图观察。"
            ),
        }

    except requests.RequestException as e:
        return {
            "success": False,
            "fallback_to_screenshot": True,
            "url": url,
            "error": f"网页请求失败：{type(e).__name__}: {e}",
        }
# ============================================================
# 工具：打开文件
# ============================================================

def open_file(target):

    path = _resolve_file_target(
        target
    )

    if not os.path.isfile(path):

        return {
            "success": False,
            "error": f"文件不存在：{path}",
        }

    try:

        os.startfile(path)

        return {
            "success": True,
            "path": path,
            "message": f"已经打开：{path}",
        }

    except Exception as e:

        return {
            "success": False,
            "path": path,
            "error":
                f"无法打开文件："
                f"{type(e).__name__}: {e}",
        }


# ============================================================
# 工具：读取文件
# ============================================================

def read_file(target):

    path = _resolve_file_target(
        target
    )

    if not os.path.isfile(path):

        return {
            "success": False,
            "error": f"文件不存在：{path}",
        }

    try:

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:

            content = f.read()

        return {
            "success": True,
            "path": path,
            "content": content,
        }

    except Exception as e:

        return {
            "success": False,
            "path": path,
            "error":
                f"读取失败："
                f"{type(e).__name__}: {e}",
        }


# ============================================================
# 工具：打开图片
# ============================================================

def open_image(path):

    path = os.path.abspath(
        path
    )

    if not os.path.isfile(path):

        return {
            "success": False,
            "error": f"图片不存在：{path}",
        }

    extensions = (
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
        ".bmp",
        ".gif",
    )

    if not path.lower().endswith(
        extensions
    ):

        return {
            "success": False,
            "error":
                "目标文件不是支持的图片格式。",
        }

    try:

        os.startfile(path)

        return {
            "success": True,
            "path": path,
            "message":
                f"已经打开图片：{path}",
        }

    except Exception as e:

        return {
            "success": False,
            "path": path,
            "error":
                f"无法打开图片："
                f"{type(e).__name__}: {e}",
        }


# ============================================================
# 工具：总力战攻略
# ============================================================

def get_raid_strategy(boss=""):

    path = KNOWLEDGE_FILES[
        "总力战攻略"
    ]

    if not os.path.isfile(path):

        return {
            "success": False,
            "error":
                f"攻略文件不存在：{path}",
        }

    try:

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:

            content = f.read().strip()

    except Exception as e:

        return {
            "success": False,
            "error":
                f"读取攻略失败："
                f"{type(e).__name__}: {e}",
        }

    if not content:

        return {
            "success": True,
            "boss": boss,
            "content":
                "总力战攻略文件目前为空。",
        }

    # --------------------------------------------------------
    # 没有指定 BOSS
    # --------------------------------------------------------

    if not boss:

        return {
            "success": True,
            "boss": "",
            "content": content,
        }

    # --------------------------------------------------------
    # 简单搜索 BOSS
    # --------------------------------------------------------

    lines = content.splitlines()

    matches = []

    current_section = []

    for line in lines:

        stripped = line.strip()

        # 用标题分隔章节
        if (
            stripped.startswith("#")
            or stripped.startswith("====")
        ):

            if current_section:

                section_text = "\n".join(
                    current_section
                )

                if boss in section_text:

                    matches.append(
                        section_text
                    )

            current_section = []

        current_section.append(line)

    # 最后一节
    if current_section:

        section_text = "\n".join(
            current_section
        )

        if boss in section_text:

            matches.append(
                section_text
            )

    # --------------------------------------------------------
    # 找到对应 BOSS
    # --------------------------------------------------------

    if matches:

        result = "\n\n".join(
            matches
        )

    else:

        # 没找到时返回全文，
        # 让模型自己判断
        result = content

    return {
        "success": True,
        "boss": boss,
        "content": result,
    }


# ============================================================
# 工具：千里眼
# ============================================================

def get_future_schedule(server=""):

    server = (
        server
        .strip()
        .lower()
    )

    if server in (
        "国际服",
        "日服",
        "日版",
        "jp",
    ):

        key = "国际服千里眼"

        display_server = "国际服"

    elif server in (
        "国服",
        "中国服",
        "cn",
    ):

        key = "国服千里眼"

        display_server = "国服"

    else:

        return {
            "success": False,
            "error":
                "server 必须是“国际服”或“国服”。",
        }

    path = KNOWLEDGE_FILES[
        key
    ]

    if not os.path.isfile(path):

        return {
            "success": False,
            "error":
                f"千里眼文件不存在：{path}",
        }

    try:

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:

            content = f.read().strip()

    except Exception as e:

        return {
            "success": False,
            "error":
                f"读取千里眼失败："
                f"{type(e).__name__}: {e}",
        }

    if not content:

        content = (
            f"{display_server}"
            "千里眼文件目前为空。"
        )

    return {
        "success": True,
        "server": display_server,
        "content": content,
    }


# ============================================================
# 工具：启动游戏
# ============================================================

# ============================================================
# 工具：启动游戏
# ============================================================

def launch_game(game):

    game = game.strip()

    path = GAME_PATHS.get(
        game
    )

    if path is None:

        return {
            "success": False,
            "error":
                f"没有配置游戏：{game}",
            "available_games":
                list(
                    GAME_PATHS.keys()
                ),
        }

    # --------------------------------------------------------
    # Steam 协议 URI（例如 CS2）
    # --------------------------------------------------------
    if path.startswith("steam://"):

        try:

            os.startfile(path)

            return {
                "success": True,
                "game": game,
                "path": path,
                "message":
                    f"正在通过 Steam 启动 {game}",
            }

        except Exception as e:

            return {
                "success": False,
                "game": game,
                "path": path,
                "error":
                    f"Steam 启动失败："
                    f"{type(e).__name__}: {e}",
            }

    # --------------------------------------------------------
    # 普通可执行文件
    # --------------------------------------------------------
    if not os.path.isfile(path):

        return {
            "success": False,
            "game": game,
            "path": path,
            "error":
                f"游戏启动器不存在：{path}",
        }

    try:

        # 使用 ShellExecuteW + runas 请求管理员权限
        # 会弹出 UAC 提示，用户确认后启动
        import ctypes

        result = ctypes.windll.shell32.ShellExecuteW(
            None,                       # hwnd
            "runas",                    # 操作：请求提权
            path,                       # 要启动的程序
            None,                       # 参数
            os.path.dirname(path),      # 工作目录
            1                           # SW_SHOWNORMAL
        )

        # ShellExecuteW 返回值 > 32 表示成功
        if result <= 32:

            return {
                "success": False,
                "game": game,
                "path": path,
                "error":
                    f"启动失败，ShellExecute 返回码：{result}",
            }

        return {
            "success": True,
            "game": game,
            "path": path,
            "message":
                f"{game} 启动器已经请求启动（需要确认 UAC 提示）。",
        }

    except Exception as e:

        return {
            "success": False,
            "game": game,
            "path": path,
            "error":
                f"启动失败："
                f"{type(e).__name__}: {e}",
        }
# ============================================================
# Tool 函数表
# ============================================================

FUNCTIONS = {

    "open_file":
        open_file,

    "read_file":
        read_file,

    "open_image":
        open_image,

    "take_screenshot":
        take_screenshot,

    "read_webpage":
        read_webpage,

    "search_web":
        search_web,

    "match_screenshot_database":
        match_screenshot,

    "get_matched_ui_elements":
        get_matched_ui_elements,

    "find_ui_element":
        find_ui_element,

    "find_web_element":
        find_web_element,

    "click_web_element":
        click_web_element,

    "wait_for_webpage":
        wait_for_webpage,

    "wait_for_page_load":
        wait_for_page_load,

    "wait_for_screen_change":
        wait_for_screen_change,

    "inspect_screen_region":
        inspect_screen_region,

    "resolve_zoomed_coordinate":
        resolve_zoomed_coordinate,

    "move_mouse":
        move_mouse,

    "click_mouse":
        click_mouse,

    "press_key":
        press_key,

    "get_raid_strategy":
        get_raid_strategy,

    "get_future_schedule":
        get_future_schedule,

    "launch_game":
        launch_game,
    "type_text":
        type_text,
    "generate_comfyui_image":
        generate_comfyui_image,
}