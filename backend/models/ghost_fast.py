from typing import Any, Dict, List

from ..thinking_engine import build_fast_steps


class GhostFast:
    mode = "fast"

    def build_response(self, query: str, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        summary = f"Быстрый ответ: по запросу '{query}' найдено {sum(s.get('count', 0) for s in sources)} упоминаний в приоритетных источниках."
        return {"text": summary, "thinking": build_fast_steps(query, sources)}
