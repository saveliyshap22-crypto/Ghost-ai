# GhostAI Realtime

Полноценное realtime веб-приложение с 3 режимами ИИ: **Ghost 1 Fast**, **Ghost 1 Pro**, **Ghost 1 Thinking**.

## Возможности
- FastAPI + WebSocket (`/ws/chat/{mode}`, `/ws/sources`)
- Socket.IO сервер (ASGI)
- Streaming ответа пословно/почастям
- Панель процесса мышления + экспорт мыслей
- Источники данных в live-режиме
- SQLite (сессии) + Redis (кэш)
- Готовые скраперы для Wikipedia, RSS News, Reddit, StackOverflow, arXiv
- Frontend: адаптивный dark UI, режимы, частицы, hotkeys `F/P/T`
- Подключены TensorFlow.js и Brain.js для расширения клиентского ИИ

## Структура
См. дерево из задания (backend/frontend/data) — реализовано полностью.

## Запуск
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000
```
Открыть: `http://localhost:8000`

## API
- `POST /api/select-mode` body: `{"mode":"fast|pro|thinking"}`
- `GET /api/thinking-process/{session_id}`
- `GET /api/stats`
- `WS /ws/chat/{mode}` payload: `{"query":"...","session_id":"..."}`
- `WS /ws/sources` live updates источников

## Демонстрационные вопросы
- Fast: `"Что нового в квантовых вычислениях?"`
- Pro: `"Сравни LLM с классическими ML-моделями"`
- Thinking: `"Как изменение климата влияет на продовольственную безопасность?"`

## Производительность и настройки
Файл `backend/CONFIG.py` содержит:
- typing speed (wpm) для каждого режима
- delay старта ответа
- приоритет и надежность источников
- Redis TTL, CORS и др.

## Примечание
Selenium/Scrapy/BeautifulSoup включены в стек и requirements; при необходимости можно расширить `backend/scrapers/` отдельными pipeline-задачами и headless browser сбором.
