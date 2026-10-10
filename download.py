#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Download and verify the local SentenceTransformer model used by Azusa Agent."""

import argparse
import os
from pathlib import Path
import sys


MODEL_ID = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_MODEL_DIR = PROJECT_DIR / "embedding_model"

CORE_FILES = (
	".gitattributes",
	"config.json",
	"config_sentence_transformers.json",
	"modules.json",
	"sentence_bert_config.json",
	"special_tokens_map.json",
	"tokenizer.json",
	"tokenizer_config.json",
	"sentencepiece.bpe.model",
	"unigram.json",
	"1_Pooling/config.json",
)


def _parse_args(argv=None):
	parser = argparse.ArgumentParser(
		description="Download and verify Azusa Agent's Hugging Face embedding model."
	)
	parser.add_argument(
		"--model-id",
		default=MODEL_ID,
		help=f"Hugging Face model repository (default: {MODEL_ID})",
	)
	parser.add_argument(
		"--output-dir",
		type=Path,
		default=DEFAULT_MODEL_DIR,
		help="Model directory (default: project_root/embedding_model)",
	)
	parser.add_argument(
		"--revision",
		default="main",
		help="Hugging Face revision or commit hash (default: main)",
	)
	parser.add_argument(
		"--endpoint",
		help="Optional Hugging Face Hub mirror, e.g. https://hf-mirror.com",
	)
	parser.add_argument(
		"--force",
		action="store_true",
		help="Force re-download files even if already cached locally.",
	)
	parser.add_argument(
		"--no-verify",
		action="store_true",
		help="Skip loading the downloaded model and running the CPU smoke test.",
	)
	return parser.parse_args(argv)


def _validate_model_files(model_dir):
	required = (
		"config.json",
		"modules.json",
		"1_Pooling/config.json",
	)
	missing = [name for name in required if not (model_dir / name).is_file()]

	has_weights = any(
		(model_dir / name).is_file()
		for name in ("model.safetensors", "pytorch_model.bin")
	)
	if not has_weights:
		missing.append("model.safetensors or pytorch_model.bin")

	has_tokenizer = any(
		(model_dir / name).is_file()
		for name in ("tokenizer.json", "sentencepiece.bpe.model", "vocab.txt")
	)
	if not has_tokenizer:
		missing.append("tokenizer.json or sentencepiece.bpe.model")

	return missing


def _download_model(model_id, model_dir, revision, endpoint=None, force=False):
	try:
		from huggingface_hub import HfApi, snapshot_download
	except ImportError as e:
		raise RuntimeError(
			"缺少 huggingface_hub。请先运行："
			"python -m pip install -r requirements.txt"
		) from e

	if endpoint:
		os.environ["HF_ENDPOINT"] = endpoint.rstrip("/")

	token = os.environ.get("HF_TOKEN") or None
	api = HfApi(endpoint=os.environ.get("HF_ENDPOINT", "https://huggingface.co"))
	model_info = api.model_info(
		repo_id=model_id,
		revision=revision,
		token=token,
	)
	remote_files = {item.rfilename for item in model_info.siblings}

	missing_core = [name for name in CORE_FILES if name not in remote_files]
	if missing_core:
		print(
			"[download] Repository is missing optional model files: "
			+ ", ".join(missing_core)
		)

	weight_file = next(
		(
			name
			for name in ("model.safetensors", "pytorch_model.bin")
			if name in remote_files
		),
		None,
	)
	if weight_file is None:
		raise RuntimeError(
			"Hugging Face 仓库没有找到 model.safetensors 或 pytorch_model.bin。"
		)

	allow_patterns = [name for name in CORE_FILES if name in remote_files]
	allow_patterns.append(weight_file)

	print(f"[download] Model: {model_id}@{revision}")
	print(f"[download] Destination: {model_dir}")
	print(f"[download] Weight: {weight_file}")
	print("[download] Optional TensorFlow/ONNX/OpenVINO weights are skipped.")

	snapshot_download(
		repo_id=model_id,
		revision=revision,
		local_dir=str(model_dir),
		allow_patterns=allow_patterns,
		ignore_patterns=[
			"tf_model.h5",
			"*.onnx",
			"*.tflite",
			"*.xml",
			"onnx/**",
			"openvino/**",
		],
		token=token,
		force_download=force,
		max_workers=4,
	)


def _verify_model(model_dir):
	missing = _validate_model_files(model_dir)
	if missing:
		raise RuntimeError(
			"模型文件不完整：" + ", ".join(missing)
		)

	try:
		from sentence_transformers import SentenceTransformer
	except ImportError as e:
		raise RuntimeError(
			"缺少 sentence-transformers。请先运行："
			"python -m pip install -r requirements.txt"
		) from e

	print("[verify] Loading model on CPU...")
	model = SentenceTransformer(str(model_dir), device="cpu")
	vector = model.encode(
		"Azusa Agent model verification",
		convert_to_numpy=True,
		show_progress_bar=False,
	)
	if getattr(vector, "ndim", 0) != 1 or vector.size == 0:
		raise RuntimeError("模型已加载，但 smoke test 没有返回有效向量。")

	print(
		f"[verify] OK: embedding dimension={vector.shape[0]}, device=cpu"
	)


def main(argv=None):
	args = _parse_args(argv)
	model_dir = args.output_dir
	if not model_dir.is_absolute():
		model_dir = PROJECT_DIR / model_dir
	model_dir = model_dir.resolve()

	try:
		missing = _validate_model_files(model_dir) if model_dir.exists() else ["model directory"]
		if missing or args.force:
			model_dir.mkdir(parents=True, exist_ok=True)
			_download_model(
				model_id=args.model_id,
				model_dir=model_dir,
				revision=args.revision,
				endpoint=args.endpoint,
				force=args.force,
			)
		else:
			print(f"[download] Model already exists: {model_dir}")

		if not args.no_verify:
			_verify_model(model_dir)

	except KeyboardInterrupt:
		print("\n[download] Cancelled. Hugging Face cache supports resuming on the next run.")
		return 130
	except Exception as e:
		print(f"[download] Failed: {type(e).__name__}: {e}")
		print("[download] Check your network/HF_ENDPOINT, then run download.py again to resume.")
		return 1

	print("[download] Ready. Start the agent with run.bat or python bridge.py.")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
