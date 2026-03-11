from typing import Any, Dict, List

from ..thinking_engine import build_pro_steps


class GhostPro:
    mode = "pro"

    def build_response(self, query: str, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        text = (
            f"Продвинутый ответ: запрос '{query}' рассмотрен по нескольким направлениям. "
            "Сопоставление показывает высокий уровень согласованности данных между энциклопедическими, новостными и техническими источниками."
        )
        return {"text": text, "thinking": build_pro_steps(query, sources)}
