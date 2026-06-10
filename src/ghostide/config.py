from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


APP_DIR = Path.home() / ".ghostide"
CONFIG_PATH = APP_DIR / "config.json"
PROJECTS_PATH = APP_DIR / "projects.json"
HISTORY_PATH = APP_DIR / "history.txt"
LOG_PATH = APP_DIR / "logs" / "ghostide.log"


@dataclass(slots=True)
class AppConfig:
    projects: list[str] = field(default_factory=list)
    active_project: str | None = None

    @classmethod
    def load(cls) -> "AppConfig":
        APP_DIR.mkdir(parents=True, exist_ok=True)
        if not PROJECTS_PATH.exists():
            return cls()
        try:
            data = json.loads(PROJECTS_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return cls()
        return cls(projects=list(data.get("projects", [])), active_project=data.get("active_project"))

    def save(self) -> None:
        APP_DIR.mkdir(parents=True, exist_ok=True)
        PROJECTS_PATH.write_text(
            json.dumps({"projects": self.projects, "active_project": self.active_project}, indent=2),
            encoding="utf-8",
        )

