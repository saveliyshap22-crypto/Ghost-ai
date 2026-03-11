import asyncio
import random
from typing import Any, AsyncGenerator, Dict, List

from .CONFIG import config


async def stream_tokens(text: str, delay_ms: int) -> AsyncGenerator[str, None]:
    for token in text.split():
        yield token + " "
        await asyncio.sleep(delay_ms / 1000)


def build_fast_steps(query: str, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {"stage": "sources", "thought": f"✓ Проверил Wikipedia для '{query}'", "sources": sources[:1]},
        {"stage": "sources", "thought": "✓ Проверил News", "sources": sources[:2]},
        {"stage": "final", "thought": "→ Готовлю ответ...", "sources": sources[:3]},
    ]


def build_pro_steps(query: str, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {"stage": "analysis", "thought": f"Анализирую запрос: {query}"},
        {"stage": "tasks", "thought": "Разбиваю на подзадачи..."},
        {"stage": "search", "thought": "Ищу информацию по источникам...", "sources": sources[:4]},
        {"stage": "compare", "thought": "Сопоставляю данные из 3 источников..."},
        {"stage": "verify", "thought": "Проверяю достоверность..."},
        {"stage": "compose", "thought": "Формулирую ответ..."},
    ]


def build_thinking_steps(query: str, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    h1 = f"Гипотеза 1: ключевой фактор запроса '{query}' подтверждается академическими данными"
    h2 = "Гипотеза 2: популярное мнение в соцсетях противоречит фактам"
    return [
        {"stage": "monologue", "thought": f"Размышляю: пользователь спрашивает о {query}, это связано с контекстом и последствиями."},
        {"stage": "hypothesis", "thought": h1, "sources": [s for s in sources if s['source'] in ['Wikipedia', 'arXiv']]},
        {"stage": "hypothesis", "thought": h2, "sources": [s for s in sources if s['source'] in ['Reddit', 'Google News RSS']]},
        {
            "stage": "compare",
            "thought": "Сравниваю источники и делаю вывод на основе наиболее надежных данных.",
            "decision": random.choice(["Wikipedia", "arXiv", "Google News RSS"]),
        },
        {"stage": "final_check", "thought": "Факт-чекинг завершен. Полнота ответа: 98%."},
    ]


async def mode_start_delay(mode: str) -> None:
    await asyncio.sleep(config.modes[mode].start_delay_sec)
