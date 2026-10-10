# -*- coding: utf-8 -*-

from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import shutil
import sqlite3
import uuid

from PIL import Image

from .settings import (
    ALLOWED_IMAGE_EXTENSIONS,
    DATABASE_PATH,
    MAX_TEMPLATE_IMAGE_BYTES,
    SCREENSHOTS_DIR,
)


def _ensure_directories():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)


@contextmanager
def _connect():
    _ensure_directories()
    connection = sqlite3.connect(DATABASE_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_db():
    _ensure_directories()
    with _connect() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS templates (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                game TEXT NOT NULL,
                image_path TEXT NOT NULL,
                width INTEGER NOT NULL CHECK(width > 0),
                height INTEGER NOT NULL CHECK(height > 0),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS ui_elements (
                id TEXT PRIMARY KEY,
                template_id TEXT NOT NULL,
                name TEXT NOT NULL,
                function TEXT NOT NULL,
                x INTEGER NOT NULL CHECK(x >= 0),
                y INTEGER NOT NULL CHECK(y >= 0),
                width INTEGER NOT NULL CHECK(width > 0),
                height INTEGER NOT NULL CHECK(height > 0),
                center_x INTEGER NOT NULL,
                center_y INTEGER NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                enabled INTEGER NOT NULL DEFAULT 1,
                notes TEXT NOT NULL DEFAULT '',
                FOREIGN KEY(template_id) REFERENCES templates(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_templates_game ON templates(game);
            CREATE INDEX IF NOT EXISTS idx_elements_template ON ui_elements(template_id);
            """
        )


def _row_to_dict(row):
    return dict(row) if row is not None else None


def _resolve_image_path(relative_path):
    return SCREENSHOTS_DIR.parent / relative_path


def _prepare_elements(elements, width, height):
    if not isinstance(elements, list):
        raise ValueError("elements 必须是列表。")

    prepared = []
    for element in elements:
        if not isinstance(element, dict):
            raise ValueError("每个 UI 元素都必须是对象。")

        name = str(element.get("name", "")).strip()
        function = str(element.get("function", "")).strip()
        if not name or not function:
            raise ValueError("每个 UI 元素都必须填写名称和功能。")

        try:
            x = int(round(float(element["x"])))
            y = int(round(float(element["y"])))
            element_width = int(round(float(element["width"])))
            element_height = int(round(float(element["height"])))
        except (KeyError, TypeError, ValueError) as e:
            raise ValueError(f"UI 坐标无效：{e}") from e

        if (
            x < 0
            or y < 0
            or element_width <= 0
            or element_height <= 0
            or x + element_width > width
            or y + element_height > height
        ):
            raise ValueError(f"UI 元素“{name}”的矩形超出原图边界。")

        prepared.append({
            "id": str(element.get("id") or f"element_{uuid.uuid4().hex[:12]}"),
            "name": name,
            "function": function,
            "x": x,
            "y": y,
            "width": element_width,
            "height": element_height,
            "center_x": x + element_width // 2,
            "center_y": y + element_height // 2,
            "description": str(element.get("description", "")).strip(),
            "enabled": 1 if element.get("enabled", True) else 0,
            "notes": str(element.get("notes", "")).strip(),
        })

    return prepared


def save_template(
    name,
    game,
    elements,
    image_path=None,
    width=None,
    height=None,
    template_id=None,
):
    name = str(name or "").strip()
    game = str(game or "").strip()
    if not name or not game:
        raise ValueError("模板名称和游戏名称不能为空。")

    init_db()
    created_image = None

    if template_id:
        existing = get_template(template_id)
        if existing is None:
            raise ValueError("要编辑的模板不存在。")
        stored_path = existing["stored_image_path"]
        width = int(width or existing["width"])
        height = int(height or existing["height"])
        if image_path:
            source = Path(image_path)
            _validate_image(source)
            width, height = _image_size(source)
            destination = _resolve_image_path(stored_path)
            if source.resolve() != destination.resolve():
                shutil.copy2(source, destination)
    else:
        if not image_path:
            raise ValueError("新建模板必须提供截图。")
        source = Path(image_path)
        _validate_image(source)
        width, height = _image_size(source)
        template_id = f"template_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        destination_name = f"{template_id}{source.suffix.lower()}"
        destination = SCREENSHOTS_DIR / destination_name
        shutil.copy2(source, destination)
        created_image = destination
        stored_path = f"screenshots/{destination_name}"

    width = int(width)
    height = int(height)
    if width <= 0 or height <= 0:
        raise ValueError("模板图片分辨率无效。")

    prepared_elements = _prepare_elements(elements, width, height)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    try:
        with _connect() as connection:
            if template_id and get_template(template_id) is not None:
                connection.execute(
                    "UPDATE templates SET name=?, game=?, width=?, height=?, updated_at=? WHERE id=?",
                    (name, game, width, height, now, template_id),
                )
                connection.execute("DELETE FROM ui_elements WHERE template_id=?", (template_id,))
            else:
                connection.execute(
                    "INSERT INTO templates(id,name,game,image_path,width,height,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)",
                    (template_id, name, game, stored_path, width, height, now, now),
                )

            connection.executemany(
                """INSERT INTO ui_elements(
                    id,template_id,name,function,x,y,width,height,center_x,center_y,
                    description,enabled,notes
                ) VALUES(:id,:template_id,:name,:function,:x,:y,:width,:height,
                         :center_x,:center_y,:description,:enabled,:notes)""",
                [dict(element, template_id=template_id) for element in prepared_elements],
            )
    except Exception:
        if created_image is not None:
            created_image.unlink(missing_ok=True)
        raise

    return get_template(template_id)


def _validate_image(path):
    if path.suffix.lower() not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError("仅支持 PNG、JPG、JPEG 和 WEBP 图片。")
    if not path.is_file() or path.stat().st_size <= 0:
        raise ValueError("截图文件不存在或为空。")
    if path.stat().st_size > MAX_TEMPLATE_IMAGE_BYTES:
        raise ValueError("截图文件不能超过 25 MB。")
    try:
        with Image.open(path) as image:
            image.verify()
    except Exception as e:
        raise ValueError(f"图片文件损坏或格式无效：{e}") from e


def _image_size(path):
    with Image.open(path) as image:
        return image.size


def get_template(template_id):
    init_db()
    with _connect() as connection:
        row = connection.execute(
            "SELECT * FROM templates WHERE id=?",
            (template_id,),
        ).fetchone()
        if row is None:
            return None
        result = _row_to_dict(row)
        result["stored_image_path"] = result["image_path"]
        result["image_path"] = str(_resolve_image_path(result["image_path"]))
        result["ui_elements"] = [
            _row_to_dict(element)
            for element in connection.execute(
                "SELECT * FROM ui_elements WHERE template_id=? ORDER BY rowid",
                (template_id,),
            ).fetchall()
        ]
        return result


def list_templates(game=None):
    init_db()
    query = """SELECT t.*, COUNT(e.id) AS ui_count FROM templates t
               LEFT JOIN ui_elements e ON e.template_id=t.id"""
    params = ()
    if game:
        query += " WHERE t.game=?"
        params = (game,)
    query += " GROUP BY t.id ORDER BY t.updated_at DESC"

    with _connect() as connection:
        templates = []
        for row in connection.execute(query, params).fetchall():
            template = _row_to_dict(row)
            template["stored_image_path"] = template["image_path"]
            template["image_path"] = str(_resolve_image_path(template["image_path"]))
            template["ui_elements"] = [
                _row_to_dict(element)
                for element in connection.execute(
                    "SELECT * FROM ui_elements WHERE template_id=? ORDER BY rowid",
                    (template["id"],),
                ).fetchall()
            ]
            templates.append(template)
        return templates


def delete_template(template_id):
    template = get_template(template_id)
    if template is None:
        return False

    with _connect() as connection:
        connection.execute("DELETE FROM templates WHERE id=?", (template_id,))

    try:
        Path(template["image_path"]).unlink(missing_ok=True)
    except OSError:
        pass
    return True
