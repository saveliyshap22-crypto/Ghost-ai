from __future__ import annotations

from pathlib import Path


SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build"}


def tree(root: Path, max_depth: int = 3) -> str:
    root = root.resolve()
    lines = [f"{root.name}/"]

    def walk(path: Path, prefix: str, depth: int) -> None:
        if depth > max_depth:
            return
        try:
            children = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
        except OSError:
            return
        visible = [child for child in children if child.name not in SKIP_DIRS]
        for index, child in enumerate(visible):
            connector = "└── " if index == len(visible) - 1 else "├── "
            lines.append(f"{prefix}{connector}{child.name}{'/' if child.is_dir() else ''}")
            if child.is_dir():
                extension = "    " if index == len(visible) - 1 else "│   "
                walk(child, prefix + extension, depth + 1)

    walk(root, "", 1)
    return "\n".join(lines)


def safe_path(project_root: Path, requested: str) -> Path:
    candidate = (project_root / requested).resolve()
    root = project_root.resolve()
    if root != candidate and root not in candidate.parents:
        raise ValueError("path escapes the active project")
    return candidate

