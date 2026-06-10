from __future__ import annotations

import hashlib
import json
import sqlite3
import time
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path

from .config import APP_DIR


@dataclass(slots=True)
class SearchResult:
    source: str
    title: str
    detail: str


class SearchEngine:
    def __init__(self, cache_path: Path | None = None) -> None:
        self.cache_path = cache_path or APP_DIR / "search-cache.sqlite"
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def search(self, query: str, project_root: Path, include_github: bool = True) -> list[SearchResult]:
        results = self.search_local(query, project_root)
        if include_github:
            results.extend(self.search_github(query))
        return results

    def search_local(self, query: str, project_root: Path) -> list[SearchResult]:
        needle = query.lower()
        results: list[SearchResult] = []
        skipped = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build"}
        for path in project_root.rglob("*"):
            if any(part in skipped for part in path.parts) or not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for line_no, line in enumerate(text.splitlines(), start=1):
                if needle in line.lower():
                    rel = path.relative_to(project_root)
                    results.append(SearchResult("local", f"{rel}:{line_no}", line.strip()))
                    break
            if len(results) >= 20:
                break
        return results

    def search_github(self, query: str) -> list[SearchResult]:
        key = "github:" + hashlib.sha256(query.encode("utf-8")).hexdigest()
        cached = self._get_cache(key)
        if cached is not None:
            return [SearchResult(**item) for item in cached]
        encoded = urllib.parse.urlencode({"q": query, "per_page": "5"})
        request = urllib.request.Request(
            f"https://api.github.com/search/repositories?{encoded}",
            headers={"Accept": "application/vnd.github+json", "User-Agent": "ghost-ide"},
        )
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            return [SearchResult("github", "GitHub search unavailable", str(exc))]
        results = [
            SearchResult(
                "github",
                item.get("full_name", "unknown"),
                item.get("description") or item.get("html_url", ""),
            )
            for item in payload.get("items", [])[:5]
        ]
        self._set_cache(key, [asdict(result) for result in results])
        return results

    def _init_db(self) -> None:
        with sqlite3.connect(self.cache_path) as conn:
            conn.execute("create table if not exists cache (key text primary key, value text not null, created real not null)")

    def _get_cache(self, key: str, ttl_seconds: int = 86_400):
        with sqlite3.connect(self.cache_path) as conn:
            row = conn.execute("select value, created from cache where key = ?", (key,)).fetchone()
        if row is None:
            return None
        value, created = row
        if time.time() - created > ttl_seconds:
            return None
        return json.loads(value)

    def _set_cache(self, key: str, value) -> None:
        with sqlite3.connect(self.cache_path) as conn:
            conn.execute(
                "insert or replace into cache (key, value, created) values (?, ?, ?)",
                (key, json.dumps(value), time.time()),
            )
