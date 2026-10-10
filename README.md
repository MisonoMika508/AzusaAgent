# AzusaAgent

**一个以白洲梓为主题的 Python AI Agent 项目，支持 AI 对话、工具调用、屏幕识别、计算机操作、语音输入与语音合成。**

**An AI agent project themed around Azusa Shirasu, featuring AI conversations, tool calling, screen recognition, computer interaction, speech input, and text-to-speech.**

**白洲アズサをテーマにした Python 製 AI エージェントプロジェクトです。AI 会話、ツール呼び出し、画面認識、PC 操作、音声入力、音声合成に対応しています。**

---

## 目录 | Contents | 目次

- [项目简介](#项目简介)
- [功能特点](#功能特点)
- [环境要求](#环境要求)
- [安装与运行](#安装与运行)
- [API 密钥配置](#api-密钥配置)
- [下载嵌入模型](#下载嵌入模型)
- [本地模型与云端 API](#本地模型与云端-api)
- [语音功能](#语音功能)
- [项目结构](#项目结构)
- [安全与隐私](#安全与隐私)
- [常见问题](#常见问题)
- [English](#english)
- [日本語](#日本語)
- [许可证](#许可证)

---

# 项目简介

AzusaAgent 是一个使用 Python 开发的 AI Agent 项目，以《蔚蓝档案》中的白洲梓为角色主题。

项目通过大语言模型、工具调用、知识检索和计算机操作功能，让 AI 不仅可以进行文本对话，还可以在获得相应权限和配置后执行指定操作。

本项目仍在开发中。部分功能依赖外部 API、本地模型、语音服务或额外的资源文件，因此克隆仓库后不一定能够立即使用全部功能。

## 功能特点

- **AI 对话：** 使用配置的大语言模型进行对话。
- **工具调用：** 由 AI 选择并调用 Python 工具完成指定任务。
- **知识检索：** 支持通过嵌入模型进行语义检索。
- **屏幕交互：** 提供屏幕截图、区域检查及鼠标键盘操作相关工具。
- **UI 辅助：** 包含 UI 数据库与 UI 编辑器相关代码。
- **语音输入：** 提供语音识别相关功能，具体使用方式取决于本地配置。
- **语音合成：** 支持配置外部 TTS 服务。
- **角色设定：** 支持通过角色配置文件定义 AI 的人设。
- **模型选择：** 项目代码包含本地模型和云端 API 相关的客户端逻辑，实际启用方式取决于当前代码配置。

请注意：仓库中存在相关代码，并不代表所有功能都已完成、经过完整测试或能在所有电脑上直接运行。

---

# 环境要求

推荐使用 Windows 10 或 Windows 11。

| 项目 | 要求 |
|---|---|
| 操作系统 | Windows 10 / Windows 11 |
| Python | 建议使用 Python 3.11，具体兼容性取决于依赖 |
| 网络 | 下载 Python 依赖、嵌入模型以及调用云端 API 时需要 |
| Git | 可使用 GitHub Desktop 管理仓库 |
| API | 使用云端模型时需要对应服务商的 API Key |
| 本地模型 | 使用 Ollama 模式时需要安装并运行 Ollama |
| 语音服务 | 取决于所启用的 STT / TTS 实现 |

部分依赖可能需要额外的系统组件。不同 Python 版本、显卡驱动及依赖版本可能会影响兼容性。

---

# 安装与运行

## 1. 下载项目

可以通过 GitHub Desktop 克隆仓库，也可以在 GitHub 页面点击 **Code → Download ZIP** 下载源代码。

仓库地址：

https://github.com/MisonoMika508/AzusaAgent

如果使用 GitHub Desktop：

1. 打开 GitHub Desktop。
2. 选择 **File → Clone repository**。
3. 选择 `MisonoMika508/AzusaAgent`。
4. 选择希望保存项目的位置。
5. 点击 **Clone**。

## 2. 安装 Python

如果电脑尚未安装 Python，请先安装合适版本的 Python，并确认可以通过终端运行：

```powershell
python --version
```

如果 `python` 命令不可用，请检查 Python 安装路径及 PATH 配置。

## 3. 创建虚拟环境

打开 PowerShell，切换到项目目录：

```powershell
cd "你的项目目录\AzusaAgent"
```

创建虚拟环境：

```powershell
python -m venv .venv
```

激活虚拟环境：

```powershell
.\.venv\Scripts\Activate.ps1
```

如果 PowerShell 阻止脚本运行，可以改用命令提示符（CMD），执行：

```bat
.venv\Scripts\activate.bat
```

## 4. 安装依赖

确保已进入项目目录，并且虚拟环境已激活：

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

如果某个依赖安装失败，请先查看错误信息，并确认 Python 版本是否受该依赖支持。

## 5. 配置 API 密钥

请根据下一节的说明创建本地 `api.txt`，不要把真实密钥提交到 GitHub。

## 6. 下载嵌入模型

依赖安装完成后，执行：

```powershell
python download.py
```

程序会下载并验证项目使用的嵌入模型。详细说明见下文。

## 7. 启动项目

当前仓库提供 `bridge.py` 作为主要程序入口。

在项目目录及正确的 Python 环境中，可以尝试：

```powershell
python bridge.py
```

具体启动方式取决于当前版本的代码和本地配置。

如果 `run.bat` 仍使用开发者电脑上的绝对路径，需要先修改它，才能在其他电脑上使用。请勿假设该启动脚本已经适用于任意安装目录。

---

# API 密钥配置

部分云端模型需要 API Key。

项目使用的密钥文件为：

```text
api.txt
```

请在本地项目根目录中创建此文件，并按照当前 `ollama_client.py` 所要求的格式填写密钥。

**请先检查当前代码读取 `api.txt` 的方式，再填写内容。不要把真实 API Key 发给其他人，也不要提交到 GitHub。**

不同服务商的 API Key 不能通用。请使用对应服务商控制台创建的密钥，并确认 API 地址、模型名称与代码配置一致。

## 为什么不直接上传 `api.txt`？

API Key 可能关联你的账户、配额或付费服务。如果泄露，其他人可能未经授权使用你的 API 额度。

因此：

- 不要上传 `api.txt`。
- 不要把 API Key 写入 README、源代码、截图或提交说明。
- 不要把 `.env` 等包含密钥的文件提交到公开仓库。
- 不要在公开 Issue 或讨论中粘贴密钥。
- 如果密钥曾经公开，立即在服务商控制台撤销或轮换该密钥。

仓库的 `.gitignore` 应排除 `api.txt`。但 `.gitignore` 只会阻止尚未被 Git 跟踪的文件；如果密钥文件以前已经提交，仅添加忽略规则并不足以从历史记录中删除它。

---

# 下载嵌入模型

本项目提供 `download.py`，用于下载、保存和验证语义检索所需的嵌入模型。

## 默认模型

模型名称：

`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

模型页面：

https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

该模型支持多语言句子嵌入，可用于语义相似度计算和检索任务。模型输出的嵌入向量维度为 384。

## 下载方法

先安装项目依赖：

```powershell
python -m pip install -r requirements.txt
```

然后运行：

```powershell
python download.py
```

默认情况下，模型会下载到项目目录下的：

```text
embedding_model/
```

该目录属于下载生成的模型资源，不需要随源代码一起上传到 GitHub。

## 可选参数

强制重新下载：

```powershell
python download.py --force
```

指定保存目录：

```powershell
python download.py --output-dir embedding_model
```

指定模型版本：

```powershell
python download.py --revision main
```

使用其他 Hugging Face 兼容镜像端点：

```powershell
python download.py --endpoint https://hf-mirror.com
```

跳过模型加载和嵌入测试：

```powershell
python download.py --no-verify
```

默认流程会在下载后验证所需文件，并尝试加载模型及生成测试嵌入。建议正常情况下保留验证步骤，以便尽早发现下载不完整或依赖异常等问题。

如果下载失败，请检查网络连接、模型仓库可访问性、磁盘空间和相关依赖版本。

---

# 本地模型与云端 API

项目代码包含本地模型和云端 API 相关逻辑，但实际运行模式由当前代码配置决定。

## 云端 API 模式

云端模式通常需要：

- 可访问对应 API 服务的网络连接。
- 有效的 API Key。
- 正确的 API 地址和模型名称。
- 服务商账户具有可用额度或权限。

云端 API 的实际费用、速率限制和数据处理方式由对应服务商的政策决定。

## Ollama 本地模型模式

本地模式需要另外安装 Ollama，并下载代码配置中指定的模型。

基本流程：

1. 安装并启动 Ollama。
2. 下载代码配置所需的模型。
3. 确认本地 Ollama 服务可以正常访问。
4. 根据项目代码切换到本地模式。
5. 启动 `bridge.py` 并测试对话。

Ollama 官方网站：

https://ollama.com/

请以仓库当前版本的 `config.py`、`ollama_client.py` 和 `bridge.py` 为准，不要假设克隆后的默认配置一定与开发者电脑上的运行配置相同。

---

# 语音功能

项目包含语音识别及语音合成相关代码，例如：

- `stt.py`：语音输入与识别相关功能。
- `tts.py`：语音合成相关功能。
- `audio_player.py`：音频播放相关功能。

实际可用的功能取决于依赖是否安装、服务是否启动，以及所需模型和权重文件是否存在。

如果使用外部语音合成服务，请根据对应服务的说明配置地址、模型和必要资源。请勿上传个人语音、私有录音或未获授权的模型文件。

---

# 项目结构

```text
AzusaAgent/
├── bridge.py
├── config.py
├── ollama_client.py
├── audio_player.py
├── stt.py
├── tts.py
├── download.py
├── requirements.txt
├── run.bat
├── test_ui_matcher.py
├── roles/
├── tools/
├── ui_database/
├── ui_editor/
├── .gitignore
└── README.md
```

说明：

| 文件或目录 | 用途 |
|---|---|
| `bridge.py` | Agent 主程序入口 |
| `config.py` | 项目配置 |
| `ollama_client.py` | 模型客户端及相关调用逻辑 |
| `audio_player.py` | 音频播放 |
| `stt.py` | 语音识别相关代码 |
| `tts.py` | 语音合成相关代码 |
| `download.py` | 下载并验证嵌入模型 |
| `requirements.txt` | Python 依赖列表 |
| `run.bat` | Windows 启动脚本 |
| `roles/` | 角色配置 |
| `tools/` | Agent 工具 |
| `ui_database/` | UI 数据相关资源或代码 |
| `ui_editor/` | UI 编辑器相关代码 |

根据实际使用情况，项目还可能需要本地知识库、向量数据库、浏览器配置、模型文件或其他资源。这些资源不一定包含在 GitHub 仓库中，需要按照代码要求单独准备。

---

# 安全与隐私

本项目可以调用鼠标、键盘、屏幕截图、文件读取或其他计算机操作工具。使用前请了解对应工具的行为和权限范围。

建议：

- 先在测试环境中验证新功能。
- 运行前检查工具允许执行的操作。
- 不要对不可信的模型输出无条件执行高风险操作。
- 不要将个人文件、浏览器资料、访问令牌或 API 密钥提交到公开仓库。
- 下载外部代码、模型和依赖时，检查来源及许可证。
- 对可能修改或删除文件的操作保留备份。

本项目按当前代码提供功能，不保证适用于所有系统环境，也不保证没有错误。请自行评估运行代码的风险。

---

# 常见问题

## 1. 启动时提示找不到模块

确认虚拟环境已经激活，并执行：

```powershell
python -m pip install -r requirements.txt
```

同时检查运行命令使用的 Python 是否为刚才安装依赖的同一个环境。

## 2. 嵌入模型下载失败

确认网络可以访问 Hugging Face，检查 `huggingface-hub` 与 `sentence-transformers` 是否正确安装，然后重新运行：

```powershell
python download.py
```

如果需要重新下载，可以使用：

```powershell
python download.py --force
```

## 3. API 调用失败

请检查：

- `api.txt` 是否存在。
- 文件内容格式是否符合当前代码要求。
- API Key 是否有效。
- API 地址与模型名称是否匹配。
- 服务商账户是否具有可用额度。
- 网络是否可以访问 API 服务。

请勿在公开问题中提交真实密钥。

## 4. 在另一台电脑上无法启动

开发环境中的绝对路径、本地模型、知识库、虚拟环境及其他资源不会因为上传 Python 源代码而自动迁移。

建议在独立目录中重新克隆仓库，创建新的虚拟环境，安装依赖，下载嵌入模型，并按照当前代码配置其他必要资源。

## 5. 为什么 GitHub 上没有模型文件？

大型模型文件、缓存、虚拟环境和个人数据通常不适合直接提交到源代码仓库。嵌入模型可以通过 `download.py` 下载到本地。

---

# English

## Overview

AzusaAgent is a Python-based AI agent project themed around Azusa Shirasu from *Blue Archive*.

It combines language-model interactions with tool calling, semantic retrieval, screen-related utilities, computer interaction, and optional speech features.

The project is under development. Some features require external APIs, local models, additional assets, or service configuration.

## Features

- AI conversations with a configurable language model.
- Python tool calling.
- Semantic retrieval using an embedding model.
- Screen capture and UI-related utilities.
- Mouse and keyboard interaction tools.
- Character configuration.
- Optional speech recognition and text-to-speech components.
- Local-model and cloud-API client logic.

The availability of each feature depends on the current code and local configuration.

## Requirements

- Windows 10 or Windows 11 is recommended.
- A compatible Python installation.
- Internet access for dependency and model downloads.
- An API key for cloud-model usage.
- Ollama and a compatible local model if local inference is enabled.
- Additional speech services or model assets when required.

## Installation

Clone the repository:

https://github.com/MisonoMika508/AzusaAgent

Open a terminal in the project directory and run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Create `api.txt` locally if required by your selected API configuration. Follow the format expected by the current source code, and never commit real API keys.

Download the embedding model:

```powershell
python download.py
```

Start the application:

```powershell
python bridge.py
```

The exact startup procedure depends on the current configuration and required local resources.

## Embedding Model

The default embedding model is:

`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

Model page:

https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

The model produces 384-dimensional sentence embeddings and supports multilingual semantic retrieval.

The downloader saves the model under `embedding_model/` by default and performs validation unless verification is disabled.

Useful options:

```powershell
python download.py --force
python download.py --output-dir embedding_model
python download.py --revision main
python download.py --endpoint https://hf-mirror.com
python download.py --no-verify
```

## Local Models and Cloud APIs

Cloud mode requires a valid API key, the correct API endpoint and model name, network access, and any required service quota.

Local mode requires Ollama and the model configured in the source code.

Check `config.py`, `ollama_client.py`, and `bridge.py` to determine which mode is enabled in the version you are using.

Ollama website: https://ollama.com/

## Security

- Never commit `api.txt`, API keys, access tokens, or private configuration files.
- If a key has been exposed, revoke or rotate it immediately.
- Review computer-control tools before running the application.
- Keep backups of important files.
- Review external model and dependency licenses.

This project is under development and is provided without a guarantee that every feature will work in every environment.

---

# 日本語

## プロジェクト概要

AzusaAgent は、『ブルーアーカイブ』の白洲アズサをテーマにした Python 製 AI エージェントプロジェクトです。

大規模言語モデルとの会話、ツール呼び出し、意味検索、画面関連機能、PC 操作、音声関連機能などを組み合わせています。

開発中のプロジェクトであり、一部の機能には外部 API、ローカルモデル、追加ファイル、各種サービスの設定が必要です。

## 主な機能

- 設定した言語モデルとの AI 会話
- Python ツールの呼び出し
- 埋め込みモデルを利用した意味検索
- スクリーンショットおよび UI 関連機能
- マウス・キーボード操作用ツール
- キャラクター設定
- 音声認識および音声合成関連機能
- ローカルモデルとクラウド API に関するクライアント処理

各機能の利用可否は、現在のソースコードとローカル環境の設定によって異なります。

## 動作環境

- Windows 10 / Windows 11 推奨
- 対応する Python 環境
- 依存パッケージとモデルをダウンロードするためのインターネット接続
- クラウドモデルを使用する場合は API キー
- ローカル推論を使用する場合は Ollama と対応モデル
- 必要に応じて音声サービスや追加モデル

## インストール

GitHub リポジトリ：

https://github.com/MisonoMika508/AzusaAgent

プロジェクトディレクトリで次のコマンドを実行します。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

必要に応じて `api.txt` をローカルに作成し、現在のソースコードが要求する形式で API キーを設定してください。実際の API キーを GitHub にアップロードしないでください。

埋め込みモデルをダウンロードします。

```powershell
python download.py
```

アプリケーションを起動します。

```powershell
python bridge.py
```

実際の起動方法は、使用する設定や追加リソースによって異なります。

## 埋め込みモデル

デフォルトモデル：

`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

モデルページ：

https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

このモデルは多言語の意味検索に利用でき、384 次元の埋め込みベクトルを生成します。

デフォルトでは `download.py` がモデルを `embedding_model/` に保存し、検証を行います。

利用可能なオプション：

```powershell
python download.py --force
python download.py --output-dir embedding_model
python download.py --revision main
python download.py --endpoint https://hf-mirror.com
python download.py --no-verify
```

## ローカルモデルとクラウド API

クラウドモードでは、有効な API キー、正しい API エンドポイントとモデル名、ネットワーク接続が必要です。

ローカルモードでは Ollama と、ソースコードで指定されたモデルが必要です。

現在の設定は `config.py`、`ollama_client.py`、`bridge.py` を確認してください。

Ollama 公式サイト：

https://ollama.com/

## セキュリティ

- `api.txt`、API キー、アクセストークン、個人設定ファイルを GitHub にアップロードしないでください。
- API キーが漏えいした場合は、直ちに無効化または再発行してください。
- PC 操作用ツールの動作を確認してから実行してください。
- 重要なファイルはバックアップしてください。
- 外部モデルと依存パッケージのライセンスを確認してください。

本プロジェクトは開発中であり、すべての機能があらゆる環境で動作することを保証するものではありません。

---

# 许可证 | License | ライセンス

请在发布前确认本项目代码、角色相关素材、外部模型、语音模型及依赖库各自的授权条件。

Unless a license file is included in this repository, no general open-source license should be assumed to apply to the project. Please add an appropriate `LICENSE` file after deciding how the project may be used, modified, and redistributed.

このリポジトリにライセンスファイルがない場合、プロジェクト全体に特定のオープンソースライセンスが適用されるとは限りません。公開・改変・再配布の条件を決めたうえで、適切な `LICENSE` ファイルを追加してください。

---

**作者 | Author | 作者：** [MisonoMika508](https://github.com/MisonoMika508)

**Repository:** https://github.com/MisonoMika508/AzusaAgent
