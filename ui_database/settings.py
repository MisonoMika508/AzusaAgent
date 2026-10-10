# -*- coding: utf-8 -*-

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "ui_database_data"
DATABASE_PATH = DATA_DIR / "database.sqlite"
SCREENSHOTS_DIR = DATA_DIR / "screenshots"

DEFAULT_GAME = "Blue Archive"
HIGH_CONFIDENCE_THRESHOLD = 0.90
LOW_CONFIDENCE_THRESHOLD = 0.75
ASPECT_RATIO_TOLERANCE = 0.015
MAX_ALIGNMENT_SHIFT_PIXELS = 1.2
DEBUG_UI_MATCH = True
MAX_TEMPLATE_IMAGE_BYTES = 25 * 1024 * 1024
ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
