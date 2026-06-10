#!/usr/bin/env python3
"""Ghost IDE one-file launcher.

Run with plain Python on Windows, Linux, or macOS:

    python ghost.py

The launcher automatically:
1. Installs missing Python dependencies (prompt-toolkit, Pygments, llama-cpp-python).
2. Downloads a small local GGUF model (<3GB VRAM) into ~/.ghostide/models if missing.
3. Starts the console IDE.
4. Shuts everything down on exit: unloads the model and kills spawned child processes.
"""

from __future__ import annotations

import atexit
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
SRC_DIR = REPO_ROOT / "src"

MODEL_DIR = Path.home() / ".ghostide" / "models"
MODEL_NAME = "qwen2.5-coder-1.5b-instruct-q4_k_m.gguf"
MODEL_URL = (
    "https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF/"
    "resolve/main/qwen2.5-coder-1.5b-instruct-q4_k_m.gguf"
)
MODEL_MIN_BYTES = 700_000_000  # sanity check against truncated downloads (~986MB full size)

REQUIRED_PACKAGES = {
    "prompt_toolkit": "prompt-toolkit>=3.0.43",
    "pygments": "Pygments>=2.17.2",
    "llama_cpp": "llama-cpp-python>=0.2.90",
}
# Prebuilt CPU wheels so Windows users don't need a C++ compiler.
LLAMA_CPP_EXTRA_INDEX = "https://abetlen.github.io/llama-cpp-python/whl/cpu"


def _ensure_dependencies() -> None:
    missing: list[tuple[str, str]] = []
    for module, requirement in REQUIRED_PACKAGES.items():
        try:
            __import__(module)
        except ImportError:
            missing.append((module, requirement))
    for module, requirement in missing:
        print(f"[setup] installing {requirement} ...")
        command = [sys.executable, "-m", "pip", "install", requirement]
        if module == "llama_cpp":
            command += ["--extra-index-url", LLAMA_CPP_EXTRA_INDEX, "--prefer-binary"]
        result = subprocess.run(command)
        if result.returncode != 0:
            if module == "llama_cpp":
                print(
                    "[setup] warning: llama-cpp-python failed to install. "
                    "Ghost IDE will still start; /ai will explain how to fix the local model runtime."
                )
                continue
            print(f"[setup] error: failed to install {requirement}")
            raise SystemExit(result.returncode)


def _download_model() -> Path | None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    model_path = MODEL_DIR / MODEL_NAME
    if model_path.exists() and model_path.stat().st_size >= MODEL_MIN_BYTES:
        return model_path
    if model_path.exists():
        print("[setup] removing incomplete model download ...")
        model_path.unlink()

    print(f"[setup] downloading local model (~1GB, one time): {MODEL_NAME}")
    print(f"[setup] from {MODEL_URL}")
    tmp_path = model_path.with_suffix(".part")

    def report(blocks: int, block_size: int, total: int) -> None:
        if total <= 0:
            return
        done = min(blocks * block_size, total)
        percent = done * 100 // total
        bar = "█" * (percent // 4) + "░" * (25 - percent // 4)
        sys.stdout.write(f"\r[setup] {bar} {percent:3d}%  {done // 1_048_576}MB / {total // 1_048_576}MB")
        sys.stdout.flush()

    try:
        urllib.request.urlretrieve(MODEL_URL, tmp_path, reporthook=report)
        print()
    except KeyboardInterrupt:
        print("\n[setup] download cancelled")
        tmp_path.unlink(missing_ok=True)
        raise SystemExit(130)
    except Exception as exc:
        print(f"\n[setup] warning: model download failed: {exc}")
        print("[setup] Ghost IDE will start without local AI; run ghost.py again with internet to retry.")
        tmp_path.unlink(missing_ok=True)
        return None

    if tmp_path.stat().st_size < MODEL_MIN_BYTES:
        print("[setup] warning: downloaded model looks truncated, discarding it.")
        tmp_path.unlink(missing_ok=True)
        return None
    tmp_path.replace(model_path)
    return model_path


def main() -> int:
    print("Ghost IDE launcher — preparing environment ...")
    _ensure_dependencies()

    model_path = _download_model()
    if model_path is not None:
        os.environ.setdefault("GHOST_IDE_MODEL", str(model_path))

    sys.path.insert(0, str(SRC_DIR))
    from ghostide.cli import GhostIDE
    from ghostide.shutdown import shutdown_everything

    app = GhostIDE()
    atexit.register(shutdown_everything, app)
    try:
        return app.run()
    finally:
        shutdown_everything(app)


if __name__ == "__main__":
    raise SystemExit(main())

