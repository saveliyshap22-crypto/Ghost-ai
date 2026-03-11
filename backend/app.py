import asyncio
import uuid
from pathlib import Path
from typing import Any, Dict

import socketio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .CONFIG import config
from .database import CacheRepository, SessionRepository, init_db
from .models.ghost_fast import GhostFast
from .models.ghost_pro import GhostPro
from .models.ghost_thinking import GhostThinking
from .scrapers.news_scraper import search_news, top_headlines
from .scrapers.reddit_scraper import search_reddit
from .scrapers.science_scraper import search_arxiv, search_stackoverflow
from .scrapers.wikipedia_scraper import search_wikipedia
from .websocket_handler import SourceBroadcaster, stream_response

init_db()
cache_repo = CacheRepository()
session_repo = SessionRepository()
source_broadcaster = SourceBroadcaster()

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
api = FastAPI(title="GhostAI Realtime")
api.add_middleware(CORSMiddleware, allow_origins=config.allowed_origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


class SelectModeRequest(BaseModel):
    mode: str


ACTIVE_MODE = {"mode": "fast"}
MODELS = {"fast": GhostFast(), "pro": GhostPro(), "thinking": GhostThinking()}


async def collect_sources(query: str) -> list[Dict[str, Any]]:
    tasks = [search_wikipedia(query), search_news(query), search_reddit(query), search_stackoverflow(query), search_arxiv(query)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    sources = []
    for item in results:
        if isinstance(item, Exception):
            continue
        sources.append(item)
    sources.extend(await top_headlines())
    await source_broadcaster.broadcast({"type": "source_update", "sources": sources})
    return sources


@api.post("/api/select-mode")
async def select_mode(payload: SelectModeRequest):
    if payload.mode not in MODELS:
        return {"ok": False, "error": "Unsupported mode"}
    ACTIVE_MODE["mode"] = payload.mode
    return {"ok": True, "mode": payload.mode, "config": config.modes[payload.mode].__dict__}


@api.get("/api/thinking-process/{session_id}")
async def get_thinking_process(session_id: str):
    return {"session_id": session_id, "thinking": session_repo.get_thinking(session_id)}


@api.get("/api/stats")
async def get_stats():
    return {"modes": {k: v.__dict__ for k, v in config.modes.items()}, "source_priority": config.source_priority}


@api.websocket("/ws/sources")
async def ws_sources(websocket: WebSocket):
    await source_broadcaster.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        source_broadcaster.disconnect(websocket)


@api.websocket("/ws/chat/{mode}")
async def ws_chat(websocket: WebSocket, mode: str):
    await websocket.accept()
    if mode not in MODELS:
        await websocket.send_json({"type": "error", "message": "Unsupported mode"})
        await websocket.close()
        return

    try:
        while True:
            data = await websocket.receive_json()
            query = data.get("query", "")
            session_id = data.get("session_id") or str(uuid.uuid4())
            cache_key = f"{mode}:{query.strip().lower()}"
            cached = await cache_repo.get(cache_key)
            if cached and mode == "fast":
                response = {"text": cached, "thinking": [{"stage": "cache", "thought": "Ответ получен из Redis кэша"}]}
                sources = [{"source": "Redis Cache", "count": 1, "reliability": "high"}]
            else:
                sources = await collect_sources(query)
                response = MODELS[mode].build_response(query, sources)
                await cache_repo.set(cache_key, response["text"])

            text = await stream_response(mode, query, websocket, response, sources)
            session_repo.save_session(session_id, mode, query, text, response["thinking"])
    except WebSocketDisconnect:
        return


@api.get("/")
async def index():
    return FileResponse("frontend/index.html")


api.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")
app = socketio.ASGIApp(sio, api)
