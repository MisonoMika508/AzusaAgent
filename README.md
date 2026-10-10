# Azusa Agent

**中文** · **English** · **日本語**

An AI desktop assistant project built with Python, featuring AI conversations, tool calling, voice interaction, and UI-related tools.

一个基于 Python 的 AI 桌面助手项目，包含 AI 对话、工具调用、语音交互和 UI 相关工具。

Python をベースにした AI デスクトップアシスタントプロジェクトです。AI との対話、ツール呼び出し、音声インタラクション、UI 関連ツールを備えています。

---

# 中文

## 项目简介

Azusa Agent 是一个持续开发中的 Python 桌面 AI 助手项目，旨在探索将 AI 模型与桌面工具、语音交互和 UI 相关功能相结合。

项目当前包含或涉及以下模块：

- **AI 对话与工具调用**：通过 AI 模型处理用户请求，并调用相应工具。
- **桌面工具**：包含文件操作及其他工具模块。
- **语音交互**：包含语音输入、音频播放和语音合成相关模块。
- **UI 工具**：包含 UI 数据库及 UI 编辑器相关代码。
- **语义检索**：使用 Sentence Transformers 模型将文本转换为向量，供语义搜索或记忆检索使用。

具体功能取决于当前代码、运行模式、外部服务及本地资源的配置。部分功能可能尚未完善。

## 项目结构

```text
AzusaAgent/
├── roles/                  # 角色配置
├── tools/                  # 工具模块
├── ui_database/            # UI 数据库相关文件
├── ui_editor/              # UI 编辑器相关文件
├── bridge.py               # 程序入口与控制逻辑
├── config.py               # 配置模块
├── ollama_client.py        # AI 客户端与交互逻辑
├── audio_player.py         # 音频播放
├── stt.py                  # 语音识别相关模块
├── tts.py                  # 语音合成相关模块
├── download.py             # 下载脚本（当前可能尚未实现）
├── requirements.txt        # Python 依赖
├── run.bat                 # Windows 启动脚本
└── README.md               # 项目说明
```

以下目录或文件可能需要在运行环境中另外准备，不一定包含在 GitHub 仓库中：

- `embedding_model/`：文本嵌入模型。
- `chroma_db/`：向量数据库或检索数据。
- `knowledge_base/`：知识库和记忆数据。
- `browser_profile/`：浏览器配置和会话数据。
- `generated_images/`：生成的图片。
- `screen_cache/`：屏幕截图或缓存数据。
- `ui_database_data/`：UI 数据或运行时数据。
- `api.txt`：本地 API 配置文件（如果当前代码需要）。

这些目录的实际用途和必需程度取决于当前代码配置。

## 环境要求

- Windows 电脑。
- 与项目依赖兼容的 Python 版本。
- 能够访问所选 AI 服务的网络环境。
- 按需安装的语音服务、模型和其他外部组件。

如果使用本地 AI 模型，还需要安装相应的本地推理软件及模型。若使用云端 API，则需要有效的 API 配置。

## 安装与运行

### 1. 下载项目

在 GitHub 仓库页面下载 ZIP，或使用 Git 克隆：

```powershell
git clone https://github.com/MisonoMika508/AzusaAgent.git
cd AzusaAgent
```

### 2. 创建 Python 虚拟环境

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

如果 PowerShell 无法激活虚拟环境，也可以直接使用虚拟环境中的 Python 执行后续命令：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3. 安装依赖

```powershell
python -m pip install -r requirements.txt
```

如果语义检索功能需要 Sentence Transformers，而依赖列表中尚未包含它，请安装：

```powershell
python -m pip install sentence-transformers
```

### 4. 下载嵌入模型

本项目使用的模型：

**`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`**

- 官方页面：https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
- 用途：文本嵌入、语义搜索和记忆检索。
- 输出向量维度：384。
- 许可证：Apache-2.0。

模型文件不会上传到本仓库，需要单独下载。

在项目根目录打开 PowerShell，并确保已经激活虚拟环境，然后执行：

```powershell
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2').save('embedding_model')"
```

下载完成后，确认 `embedding_model/` 目录已经生成。

首次下载需要网络连接，可能需要等待一段时间。下载后应确认模型加载路径与 `config.py`、`bridge.py` 或实际模型加载代码中的路径一致。

### 5. 配置 API 密钥

如果当前运行模式需要 API 密钥，请在项目根目录创建本地 `api.txt`，按照当前代码要求填写密钥。

**请勿将真实 API 密钥上传到 GitHub。**

如果项目要求其他配置格式或 API 服务地址，请以实际代码为准。

### 6. 启动程序

确认依赖、模型及必要配置已经准备好后，在项目根目录运行：

```powershell
python bridge.py
```

如果 `run.bat` 已经按照当前环境配置完成，也可以尝试运行该文件。

首次运行前，请检查程序是否还依赖仓库外的目录或文件。仅下载 GitHub 仓库并不保证所有功能都能立即运行。

## 外部模型与服务

| 组件 | 用途 | 是否需要 |
|---|---|---|
| Sentence Transformers 模型 | 文本嵌入和语义检索 | 使用相关检索功能时 |
| AI API | 云端 AI 对话 | 使用云端模式时 |
| Ollama 与本地模型 | 本地 AI 推理 | 使用本地模式时 |
| 语音服务和模型 | 语音输入、语音合成 | 使用对应语音功能时 |
| UI 数据和缓存 | UI 相关功能 | 根据具体功能而定 |

请从各组件的官方页面获取模型和软件，并遵守各自的许可证和使用条款。

## 安全与隐私

- 不要上传 `api.txt`、`.env` 或任何真实 API 密钥。
- 不要上传包含账号、Cookie 或登录状态的 `browser_profile/`。
- 不要上传私人记忆、个人资料或敏感知识库文件。
- 不要将截图缓存、日志或私人生成内容默认公开。
- 不要上传 `.venv/`、`__pycache__/` 和大型模型文件。
- 在公开提交代码之前，请检查文件内容及 Git 提交历史。

如果 API 密钥曾经被公开，应立即在相应服务平台撤销并重新生成。

## 项目状态

本项目仍在开发中。功能、依赖和安装方式可能发生变化。欢迎提交问题报告、建议和改进。

## 许可证

本仓库的许可证以根目录的 `LICENSE` 文件为准。如果尚未提供 `LICENSE`，请不要假设项目代码已经允许他人自由复制、修改或再发布。

---

# English

## About

Azusa Agent is a Python desktop AI assistant project under active development. It explores the integration of AI models with desktop tools, voice interaction, and UI-related functionality.

Current project areas include:

- **AI conversations and tool calling**
- **Desktop tools**, including file-related operations
- **Voice interaction**, including speech input, audio playback, and speech synthesis modules
- **UI tools**, including a UI database and editor
- **Semantic retrieval**, using Sentence Transformers to generate text embeddings

Available functionality depends on the source code, runtime configuration, external services, and local resources. Some features may still be incomplete.

## Requirements

- A Windows PC.
- A Python version compatible with the project dependencies.
- Network access to the selected AI service.
- Additional models or services for optional features.

Local-model mode requires the appropriate inference software and model. Cloud API mode requires a valid API configuration.

## Installation

### 1. Download the repository

```powershell
git clone https://github.com/MisonoMika508/AzusaAgent.git
cd AzusaAgent
```

### 2. Create a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

If Sentence Transformers is needed but is not already listed in `requirements.txt`, install it separately:

```powershell
python -m pip install sentence-transformers
```

### 4. Download the embedding model

The project uses:

**`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`**

- Official model page: https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
- Purpose: text embeddings and semantic retrieval.
- Embedding dimension: 384.
- License: Apache-2.0.

The model files are not included in this repository.

From the project root, run:

```powershell
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2').save('embedding_model')"
```

Verify that `embedding_model/` exists after downloading. Make sure its location matches the model path expected by the source code.

The initial download requires an internet connection and may take some time.

### 5. Configure the API key

If the selected runtime mode requires an API key, create a local `api.txt` file in the project root and follow the format expected by the source code.

**Never upload real API keys to GitHub.**

### 6. Run the application

After preparing the dependencies, model, and required configuration, run:

```powershell
python bridge.py
```

You may also try `run.bat` if it is configured for your environment.

Some runtime resources may be stored outside the repository. Cloning the repository alone does not guarantee that every feature will work immediately.

## External Models and Services

| Component | Purpose | Required when |
|---|---|---|
| Sentence Transformers model | Text embeddings and semantic retrieval | Using retrieval features |
| AI API | Cloud-based AI conversations | Using cloud mode |
| Ollama and a local model | Local AI inference | Using local mode |
| Voice services and models | Speech input and synthesis | Using the corresponding voice features |
| UI data and caches | UI-related features | Depending on the feature |

Obtain external components from their official sources and follow their respective licenses and terms.

## Security and Privacy

- Never upload `api.txt`, `.env`, or real API keys.
- Do not upload `browser_profile/` if it contains cookies, account data, or login sessions.
- Do not publish private memories, personal information, or sensitive knowledge-base files.
- Review screenshots, logs, and generated content before publishing.
- Exclude `.venv/`, `__pycache__/`, and large model files from version control.
- Review file contents and commit history before making the repository public.

If an API key has been exposed, revoke it and generate a replacement immediately.

## Project Status

This project is under active development. Features, dependencies, and setup instructions may change. Bug reports, suggestions, and improvements are welcome.

## License

Refer to the `LICENSE` file in the repository root. If no license is provided, do not assume that others are permitted to freely copy, modify, or redistribute the code.

---

# 日本語

## プロジェクトについて

Azusa Agent は、開発中の Python 製 AI デスクトップアシスタントプロジェクトです。AI モデルとデスクトップ操作ツール、音声インタラクション、UI 関連機能の連携を目指しています。

主な機能分野：

- **AI との対話とツール呼び出し**
- **デスクトップツール**：ファイル関連の操作など
- **音声インタラクション**：音声入力、音声再生、音声合成に関連するモジュール
- **UI ツール**：UI データベースとエディター
- **意味検索**：Sentence Transformers によるテキストのベクトル化

利用できる機能は、ソースコード、実行設定、外部サービス、ローカルリソースによって異なります。一部の機能は未完成の場合があります。

## 動作環境

- Windows PC
- プロジェクトの依存関係に対応する Python
- 使用する AI サービスに接続できるネットワーク
- オプション機能に必要な追加モデルやサービス

ローカルモデルモードでは、対応する推論ソフトウェアとモデルが必要です。クラウド API モードでは、有効な API 設定が必要です。

## インストール

### 1. リポジトリを取得

```powershell
git clone https://github.com/MisonoMika508/AzusaAgent.git
cd AzusaAgent
```

### 2. 仮想環境を作成

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. 依存関係をインストール

```powershell
python -m pip install -r requirements.txt
```

Sentence Transformers が必要で、まだ依存関係に含まれていない場合は、別途インストールしてください。

```powershell
python -m pip install sentence-transformers
```

### 4. 埋め込みモデルをダウンロード

本プロジェクトでは次のモデルを使用します。

**`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`**

- 公式ページ：https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
- 用途：テキストのベクトル化と意味検索
- ベクトル次元数：384
- ライセンス：Apache-2.0

モデル本体はリポジトリに含まれていません。

プロジェクトのルートディレクトリで次のコマンドを実行してください。

```powershell
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2').save('embedding_model')"
```

ダウンロード後、`embedding_model/` が作成されていることを確認してください。保存先はソースコードが要求するモデルの読み込みパスと一致している必要があります。

初回のダウンロードにはインターネット接続が必要で、時間がかかる場合があります。

### 5. API キーを設定

実行モードで API キーが必要な場合は、プロジェクトのルートディレクトリにローカルの `api.txt` を作成し、ソースコードが要求する形式で設定してください。

**実際の API キーを GitHub にアップロードしないでください。**

### 6. 起動

依存関係、モデル、必要な設定を準備した後、次のコマンドで起動します。

```powershell
python bridge.py
```

環境に合わせて設定されている場合は、`run.bat` も使用できます。

実行に必要なリソースの一部がリポジトリ外に保存されている場合があります。リポジトリを取得しただけでは、すべての機能がすぐに動作するとは限りません。

## 外部モデルとサービス

| コンポーネント | 用途 | 必要になる場合 |
|---|---|---|
| Sentence Transformers モデル | テキストのベクトル化と意味検索 | 検索機能を使用する場合 |
| AI API | クラウド AI との対話 | クラウドモードを使用する場合 |
| Ollama とローカルモデル | ローカル AI 推論 | ローカルモードを使用する場合 |
| 音声サービスとモデル | 音声入力・音声合成 | 該当する音声機能を使用する場合 |
| UI データとキャッシュ | UI 関連機能 | 機能に応じて必要 |

外部コンポーネントは公式配布元から入手し、それぞれのライセンスと利用規約に従ってください。

## セキュリティとプライバシー

- `api.txt`、`.env`、実際の API キーをアップロードしないでください。
- Cookie、アカウント情報、ログイン状態を含む `browser_profile/` を公開しないでください。
- 個人の記憶データ、個人情報、機密性のある知識ベースを公開しないでください。
- スクリーンショット、ログ、生成したコンテンツを公開前に確認してください。
- `.venv/`、`__pycache__/`、大容量モデルを Git の管理対象から除外してください。
- リポジトリを公開する前に、ファイル内容とコミット履歴を確認してください。

API キーが公開された場合は、直ちに無効化し、新しいキーを発行してください。

## 開発状況

本プロジェクトは開発中です。機能、依存関係、セットアップ手順は変更される場合があります。不具合報告、提案、改善への協力を歓迎します。

## ライセンス

適用されるライセンスについては、リポジトリのルートにある `LICENSE` ファイルを確認してください。ライセンスがない場合、自由な複製、改変、再配布が許可されていると想定しないでください。
