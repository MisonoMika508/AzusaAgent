# -*- coding: utf-8 -*-

from pathlib import Path
import sys
import uuid

from flask import Flask, jsonify, render_template, request, send_from_directory
from PIL import Image

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from ui_database.database import (
    delete_template,
    get_template,
    init_db,
    list_templates,
    save_template,
)
from ui_database.settings import (
    ALLOWED_IMAGE_EXTENSIONS,
    MAX_TEMPLATE_IMAGE_BYTES,
)


APP_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = APP_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
_UPLOADS = {}

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["MAX_CONTENT_LENGTH"] = MAX_TEMPLATE_IMAGE_BYTES
init_db()


def _template_payload(template):
    return {
        "id": template["id"],
        "name": template["name"],
        "game": template["game"],
        "width": template["width"],
        "height": template["height"],
        "created_at": template["created_at"],
        "updated_at": template["updated_at"],
        "ui_count": template.get("ui_count", len(template.get("ui_elements", []))),
        "image_url": f"/api/templates/{template['id']}/image",
        "ui_elements": template.get("ui_elements", []),
    }


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/templates")
def api_templates():
    return jsonify([_template_payload(item) for item in list_templates()])


@app.get("/api/templates/<template_id>")
def api_get_template(template_id):
    template = get_template(template_id)
    if template is None:
        return jsonify({"error": "模板不存在。"}), 404
    return jsonify(_template_payload(template))


@app.get("/api/templates/<template_id>/image")
def api_template_image(template_id):
    template = get_template(template_id)
    if template is None:
        return jsonify({"error": "模板不存在。"}), 404
    path = Path(template["image_path"])
    return send_from_directory(path.parent, path.name, conditional=True)


@app.post("/api/upload")
def api_upload():
    uploaded = request.files.get("image")
    if uploaded is None or not uploaded.filename:
        return jsonify({"error": "请选择截图文件。"}), 400

    suffix = Path(uploaded.filename).suffix.lower()
    if suffix not in ALLOWED_IMAGE_EXTENSIONS:
        return jsonify({"error": "只支持 PNG、JPG、JPEG 和 WEBP。"}), 400

    upload_id = uuid.uuid4().hex
    path = UPLOAD_DIR / f"{upload_id}{suffix}"
    try:
        uploaded.save(path)
        if path.stat().st_size <= 0 or path.stat().st_size > MAX_TEMPLATE_IMAGE_BYTES:
            path.unlink(missing_ok=True)
            return jsonify({"error": "图片为空或超过 25 MB。"}), 400
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            width, height = image.size
    except Exception as e:
        path.unlink(missing_ok=True)
        return jsonify({"error": f"图片无效：{type(e).__name__}: {e}"}), 400

    _UPLOADS[upload_id] = path
    return jsonify({
        "upload_id": upload_id,
        "width": width,
        "height": height,
        "image_url": f"/api/uploads/{upload_id}",
    })


@app.get("/api/uploads/<upload_id>")
def api_uploaded_image(upload_id):
    path = _UPLOADS.get(upload_id)
    if path is None or not path.is_file():
        return jsonify({"error": "临时图片不存在，请重新上传。"}), 404
    return send_from_directory(path.parent, path.name, conditional=True)


@app.post("/api/save")
def api_save_template():
    payload = request.get_json(silent=True) or {}
    template_id = str(payload.get("template_id") or "").strip() or None
    upload_id = str(payload.get("upload_id") or "").strip()
    image_path = _UPLOADS.get(upload_id) if upload_id else None

    if template_id and get_template(template_id) is None:
        return jsonify({"error": "要编辑的模板不存在。"}), 404
    if not template_id and image_path is None:
        return jsonify({"error": "请先上传截图。"}), 400

    try:
        template = save_template(
            name=payload.get("name", ""),
            game=payload.get("game", "Blue Archive"),
            elements=payload.get("ui_elements", []),
            image_path=str(image_path) if image_path else None,
            template_id=template_id,
        )
    except (ValueError, OSError) as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        app.logger.exception("保存 UI 模板失败")
        return jsonify({"error": f"保存失败：{type(e).__name__}: {e}"}), 500

    if upload_id:
        uploaded_path = _UPLOADS.pop(upload_id, None)
        if uploaded_path:
            uploaded_path.unlink(missing_ok=True)

    return jsonify(_template_payload(template))


@app.delete("/api/templates/<template_id>")
def api_delete_template(template_id):
    if not delete_template(template_id):
        return jsonify({"error": "模板不存在。"}), 404
    return jsonify({"success": True})


@app.errorhandler(413)
def request_too_large(_error):
    return jsonify({"error": "图片不能超过 25 MB。"}), 413


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
