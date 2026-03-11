import asyncio
from typing import Any, Dict, List

from fastapi import WebSocket

from .CONFIG import config
from .thinking_engine import mode_start_delay, stream_tokens


class SourceBroadcaster:
    def __init__(self) -> None:
        self.clients: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.clients.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self.clients.discard(websocket)

    async def broadcast(self, payload: Dict[str, Any]) -> None:
        dead = []
        for ws in self.clients:
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


async def stream_response(mode: str, query: str, websocket: WebSocket, response: Dict[str, Any], sources: List[Dict[str, Any]]) -> str:
    await mode_start_delay(mode)
    mode_cfg = config.modes[mode]

    for idx, step in enumerate(response["thinking"]):
        await websocket.send_json({"type": "thinking", "step": step, "progress": int((idx + 1) / len(response['thinking']) * 100)})
        await asyncio.sleep(0.15)

    final_text = ""
    packet_type = "word" if mode == "fast" else ("chunk" if mode == "pro" else "thinking_step")
    async for token in stream_tokens(response["text"], mode_cfg.websocket_delay_ms):
        final_text += token
        await websocket.send_json(
            {
                "type": packet_type,
                "content": token,
                "delay": mode_cfg.websocket_delay_ms,
                "sources": sources,
            }
        )

    await websocket.send_json({"type": "done", "mode": mode})
    return final_text.strip()
