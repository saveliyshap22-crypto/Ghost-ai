from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class ModeConfig:
    name: str
    color: str
    start_delay_sec: float
    typing_wpm: tuple[int, int]
    websocket_delay_ms: int


@dataclass
class AppConfig:
    sqlite_path: str = "data/knowledge_base.db"
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_sec: int = 3600
    allowed_origins: List[str] = field(default_factory=lambda: ["*"])
    source_priority: List[Dict[str, str]] = field(
        default_factory=lambda: [
            {"name": "Wikipedia", "reliability": "high"},
            {"name": "Google News RSS", "reliability": "high"},
            {"name": "Reddit (AskScience/ELI5)", "reliability": "medium"},
            {"name": "Stack Overflow", "reliability": "medium"},
            {"name": "arXiv", "reliability": "high"},
            {"name": "BBC RSS", "reliability": "high"},
            {"name": "Reuters RSS", "reliability": "high"},
        ]
    )
    modes: Dict[str, ModeConfig] = field(
        default_factory=lambda: {
            "fast": ModeConfig("Ghost 1 Fast", "#00ff88", 0.7, (50, 80), 20),
            "pro": ModeConfig("Ghost 1 Pro", "#6c63ff", 2.0, (30, 50), 40),
            "thinking": ModeConfig("Ghost 1 Thinking", "#00d4ff", 3.5, (20, 40), 60),
        }
    )


config = AppConfig()
