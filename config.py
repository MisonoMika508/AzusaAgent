# -*- coding: utf-8 -*-

import os


# ============================================================
# Agent 根目录
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ============================================================
# Ollama
# ============================================================

OLLAMA_URL = "http://127.0.0.1:11434"
OLLAMA_BASE_URL = OLLAMA_URL + "/v1"

OLLAMA_MODEL = "richardyoung/qwen2.5-7b-instruct-abliterated:latest"
# =========================
# Agent
# =========================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

ROLE_FILE = os.path.join(
    BASE_DIR,
    "roles",
    "Azusa.json"
)

SKILL_FILE = os.path.join(
    BASE_DIR,
    "knowledge_base",
    "skill.txt"
)

MEMORY_FILE = os.path.join(
    BASE_DIR,
    "knowledge_base",
    "白洲梓_记忆.txt"
)

EMBEDDING_MODEL_PATH = os.path.join(
    BASE_DIR,
    "embedding_model"
)

CHROMA_DB_PATH = os.path.join(
    BASE_DIR,
    "chroma_db"
)

MAX_RETRIEVAL_RESULTS = 3


# =========================
# Agent 文件权限
# =========================

ALLOWED_PATHS = [
    BASE_DIR,
]


# =========================
# 固定文件
# =========================

FIXED_FILES = {
    "azusa_role": ROLE_FILE,
    "skill": SKILL_FILE,
    "memory": MEMORY_FILE,
}

# ============================================================
# 角色
# ============================================================

ROLE_FILE = os.path.join(
    BASE_DIR,
    "roles",
    "Azusa.json"
)


# ============================================================
# Skill
# ============================================================

SKILL_FILE = os.path.join(
    BASE_DIR,
    "knowledge_base",
    "skill.txt"
)


# ============================================================
# RAG 记忆
# ============================================================

MEMORY_FILE = os.path.join(
    BASE_DIR,
    "knowledge_base",
    "白洲梓_记忆.txt"
)

EMBEDDING_MODEL_PATH = os.path.join(
    BASE_DIR,
    "embedding_model"
)

CHROMA_DB_PATH = os.path.join(
    BASE_DIR,
    "chroma_db"
)

MAX_RETRIEVAL_RESULTS = 3


# ============================================================
# Agent 文件权限
# ============================================================

# 只允许 Agent 操作这些目录
ALLOWED_PATHS = [
    BASE_DIR,

    # 以后你的游戏目录可以加在这里
    # r"D:\Games\你的游戏",
]


# ============================================================
# 固定文件
# ============================================================
#
# Agent 不需要自己猜路径。
#
# 你可以提前给它定义：
#
# "azusa_role" -> Azusa.json
# "skill"      -> skill.txt
# "memory"     -> 白洲梓_记忆.txt
#
# 后面游戏文件也可以这样添加。
#

FIXED_FILES = {
    "azusa_role": ROLE_FILE,

    "skill": SKILL_FILE,

    "memory": MEMORY_FILE,

    # 示例：
    # "game_config": r"D:\Games\MyGame\Config\config.json",
    # "game_log": r"D:\Games\MyGame\Logs\game.log",
}


# ============================================================
# GPT-SoVITS
# ============================================================

GPT_SOVITS_URL = "http://127.0.0.1:9872/"

REF_AUDIO = r"D:\Azusa\AzusaSwimsuit_Lobby_4.wav"

REF_LANGUAGE = "中文"

# GPT-SoVITS WebUI 启动脚本
GPT_SOVITS_BAT = (
    r"D:\OTHERS\GPT-SoVITS\GPT-SoVITS-v3lora-20250228"
    r"\GPT-SoVITS-v3lora-20250228\go-webui.bat"
)

# ============================================================
# GPT-SoVITS 权重
# ============================================================

GPT_MODEL = r"D:\OTHERS\GPT-SoVITS\GPT-SoVITS-v3lora-20250228\GPT-SoVITS-v3lora-20250228\GPT_weights_v2\Zi_BaiZhou-e15.ckpt"

SOVITS_MODEL = r"D:\OTHERS\GPT-SoVITS\GPT-SoVITS-v3lora-20250228\GPT-SoVITS-v3lora-20250228\SoVITS_weights_v2\Zi_BaiZhou_e16_s256.pth"


# ============================================================
# Agent
# ============================================================

AGENT_MAX_HISTORY = 10

AGENT_TEMPERATURE = 0.4

AGENT_MAX_TOKENS = 512