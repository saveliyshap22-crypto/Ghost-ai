from typing import Any, Dict, List

from ..thinking_engine import build_thinking_steps


class GhostThinking:
    mode = "thinking"

    def build_response(self, query: str, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        text = (
            f"Глубокий вывод по теме '{query}': наиболее достоверная линия аргументации поддерживается "
            "источниками с высокой надежностью, тогда как социальные обсуждения дают полезный, но менее стабильный контекст."
        )
        return {"text": text, "thinking": build_thinking_steps(query, sources)}
