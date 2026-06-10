from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


TEXT_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".json",
    ".md",
    ".toml",
    ".yaml",
    ".yml",
    ".txt",
    ".css",
    ".html",
    ".go",
    ".rs",
    ".java",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
}


@dataclass(slots=True)
class AIConfig:
    model_path: Path | None = None
    max_context_files: int = 8
    max_context_bytes: int = 24_000
    max_tokens: int = 512

    @classmethod
    def from_environment(cls) -> "AIConfig":
        raw_model = os.environ.get("GHOST_IDE_MODEL")
        if raw_model:
            return cls(model_path=Path(raw_model).expanduser())
        return cls(model_path=_discover_default_model())


def _discover_default_model() -> Path | None:
    """Pick up a model downloaded by ghost.py (~/.ghostide/models/*.gguf)."""
    models_dir = Path.home() / ".ghostide" / "models"
    if not models_dir.exists():
        return None
    candidates = sorted(models_dir.glob("*.gguf"), key=lambda p: p.stat().st_size, reverse=True)
    return candidates[0] if candidates else None


class LocalAIAssistant:
    """Offline-first adapter for GGUF models through optional llama-cpp-python."""

    def __init__(self, config: AIConfig | None = None) -> None:
        self.config = config or AIConfig.from_environment()
        self._llm = None
        self._load_error: str | None = None

    def ask(self, question: str, project_root: Path) -> str:
        prompt = self._build_prompt(question, project_root)
        llm = self._load_llm()
        if llm is None:
            return (
                "Local AI is not configured yet.\n\n"
                "Easiest fix: run `python ghost.py` — it installs llama-cpp-python and downloads "
                "a small local GGUF model (Qwen2.5-Coder 1.5B, fits in <3GB VRAM) automatically.\n"
                "Manual setup: pip install 'ghost-ide[ai]' and set GHOST_IDE_MODEL=/path/to/model.gguf.\n\n"
                f"Question captured with project context:\n{question}\n\n"
                f"Runtime detail: {self._load_error or 'no model path configured'}"
            )

        response = llm(
            prompt,
            max_tokens=self.config.max_tokens,
            stop=["</s>", "User:", "\n/"],
            echo=False,
        )
        return response["choices"][0]["text"].strip()

    def _load_llm(self):
        if self._llm is not None:
            return self._llm
        if not self.config.model_path:
            self._load_error = "GHOST_IDE_MODEL is not set"
            return None
        if not self.config.model_path.exists():
            self._load_error = f"model file does not exist: {self.config.model_path}"
            return None
        try:
            from llama_cpp import Llama
        except Exception as exc:  # pragma: no cover - optional dependency
            self._load_error = f"llama-cpp-python is unavailable: {exc}"
            return None
        self._llm = Llama(
            model_path=str(self.config.model_path),
            n_ctx=4096,
            n_threads=max(1, os.cpu_count() or 1),
            verbose=False,
        )
        return self._llm

    def close(self) -> None:
        """Unload the model and free its memory (called on IDE shutdown)."""
        llm = self._llm
        self._llm = None
        if llm is None:
            return
        try:
            close = getattr(llm, "close", None)
            if callable(close):
                close()
        finally:
            del llm

    def _build_prompt(self, question: str, project_root: Path) -> str:
        context = self._collect_project_context(project_root)
        return (
            "You are Ghost IDE's local coding assistant. Answer concisely and use the "
            "provided project context. If information is missing, say what to inspect next.\n\n"
            f"Project root: {project_root}\n\n"
            f"{context}\n\n"
            f"User: {question}\nAssistant:"
        )

    def _collect_project_context(self, project_root: Path) -> str:
        parts: list[str] = []
        remaining = self.config.max_context_bytes
        skipped_dirs = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build"}
        for path in sorted(project_root.rglob("*")):
            if len(parts) >= self.config.max_context_files or remaining <= 0:
                break
            if any(part in skipped_dirs for part in path.parts):
                continue
            if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            snippet = text[: min(len(text), max(0, remaining))]
            remaining -= len(snippet)
            rel = path.relative_to(project_root)
            parts.append(f"--- {rel} ---\n{snippet}")
        return "\n\n".join(parts) if parts else "No text project files found."
