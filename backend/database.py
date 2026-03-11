import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import redis.asyncio as redis

from .CONFIG import config


Path("data").mkdir(exist_ok=True)


@contextmanager
def get_db():
    conn = sqlite3.connect(config.sqlite_path)
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                mode TEXT NOT NULL,
                query TEXT NOT NULL,
                response TEXT,
                thinking_json TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


class SessionRepository:
    def save_session(self, session_id: str, mode: str, query: str, response: str, thinking: List[Dict[str, Any]]) -> None:
        with get_db() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO sessions(session_id, mode, query, response, thinking_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (session_id, mode, query, response, json.dumps(thinking, ensure_ascii=False), datetime.utcnow().isoformat()),
            )
            conn.commit()

    def get_thinking(self, session_id: str) -> List[Dict[str, Any]]:
        with get_db() as conn:
            row = conn.execute("SELECT thinking_json FROM sessions WHERE session_id = ?", (session_id,)).fetchone()
            if not row:
                return []
            return json.loads(row[0] or "[]")


class CacheRepository:
    def __init__(self) -> None:
        self.redis = redis.from_url(config.redis_url, decode_responses=True)

    async def get(self, key: str) -> str | None:
        try:
            return await self.redis.get(key)
        except Exception:
            return None

    async def set(self, key: str, value: str) -> None:
        try:
            await self.redis.set(key, value, ex=config.cache_ttl_sec)
        except Exception:
            pass
