# Отчет ревью проекта bybit_options

Дата: 2025-02-14

## 1) Структура проекта (основные блоки)

**Backend (Python)**
- `api_example.py` — FastAPI API, точки входа для портфеля, доски опционов, истории и стратегии.
- `main.py` — CLI запуск анализа риска.
- `bybit_connector.py` — асинхронный клиент Bybit API.
- `market_data_service.py` — сбор и кеширование рыночных данных.
- `risk_engine.py`, `analysis_orchestrator.py`, `data_models.py` — расчетная логика, сборка портфеля и модели данных.
- `trade_logger.py` — логирование сделок и учет entry IV (PostgreSQL).
- `database.py`, `iv_rank_service.py` — доступ к БД для истории цен/IV Rank.
- `websocket_manager.py`, `stream_manager.py` — WebSocket инфраструктура и стримы.

**Frontend (React/Vite)**
- `frontend/src` — UI компонентов (Options Board, Portfolio, Charts, Trade Log), Zustand store, API/WebSocket клиенты.
- `frontend/src/services/api.ts` — REST клиент и кеширование.
- `frontend/src/services/websocket.ts` — WebSocket клиент.
- `frontend/src/services/export.ts` — локальный экспорт.
- `frontend/src/stores/portfolioStore.ts` — состояние UI и интеграции.

**Инфраструктура и запуск**
- `docker-compose.yml`, `Dockerfile.backend`, `frontend/Dockerfile` — контейнеризация.
- `startup.sh`, `README_START.md` — локальный запуск.

**Документация/артефакты**
- Технические отчеты и планы: `README_START.md`, `implementation_summary.md`, `CURRENT_IMPLEMENTATION_AUDIT.md`, и др.

## 2) Что готово

**Backend**
- Базовый сбор позиций и маржи через `BybitConnector` и `MarketDataService`.
- Расчет риск-метрик (Greeks, Gamma Rent, IV metrics) и сборка портфеля.
- REST эндпоинты:
  - `/api/v1/risk/portfolio`, `/api/v1/risk/coin/{coin}`
  - `/api/v1/margin`, `/api/v1/positions`
  - `/api/v1/options-board`
  - `/api/v1/price-history`, `/api/v1/iv-rank`
  - `/api/v1/strategy/*`
- WebSocket инфраструктура (менеджер подключений, базовые типы сообщений).

**Frontend**
- UI-скелет и основные страницы/виджеты портфеля и доски опционов.
- Реализован state management (Zustand), запросы к API, кеширование, базовые графики.
- Локальный экспорт (json/md/csv) в `portfolioStore.ts`.

**Инфраструктура**
- Docker Compose для backend + frontend + Redis + TimescaleDB.
- Скрипт запуска `startup.sh`.

## 3) Что не готово / частично готово

**Backend**
- Нет эндпоинтов, на которые ссылается фронтенд:
  - `/api/v1/payoff-chart`, `/api/v1/trade-log`, `/api/v1/export`, `/api/v1/greeks/summary`, `/api/v1/iv-history`.
- WebSocket рассылка не запускается автоматически (нет запуска broadcast loop).
- Интеграция REST snapshot для orderbook resync в `stream_manager.py` не реализована.
- Исторические данные (IV Rank/цены) требуют ручного backfill.

**Frontend**
- Payoff chart, trade log, export через API — отключены, используются mock/локальные данные.
- Часть подписок WebSocket не соответствует серверной логике (см. ошибки ниже).

**Автозапуск**
- Автозапуск backend описан только для VS Code (`.vscode/tasks.json`), frontend не стартует автоматически.
- В Docker Compose запуск зависит от корректных env и сетевых адресов (см. ошибки ниже).

## 4) Ошибки и риски (с решениями)

1) **Backend не стартует при установке зависимостей из `requirements.txt`**
- Причина: `fastapi` и `uvicorn` закомментированы в `requirements.txt`.
- Симптом: `ModuleNotFoundError: fastapi` при запуске `api_example.py`.
- Решение: включить `fastapi` и `uvicorn[standard]` в `requirements.txt` или выделить отдельный `requirements.api.txt`.
- Файлы: `requirements.txt`.

2) **`DATABASE_URL` обязателен уже на импорте `database.py`**
- Причина: при отсутствии `DATABASE_URL` выполняется `raise ValueError` на уровне модуля.
- Симптом: API не стартует вообще, даже если пользователю не нужны исторические данные.
- Решение: перенос проверки в `init_db()` или разрешить запуск без БД (ленивое подключение, флаг конфигурации).
- Файлы: `database.py`.

3) **`/api/v1/positions` зависит от таблицы `position_entries`, которая не создается в `init_db()`**
- Причина: таблица создается только в `TradeLogger.initialize()`.
- Симптом: запрос к `/api/v1/positions` может падать в рантайме, если trade logger не запускался.
- Решение: миграция/инициализация таблицы при старте API или graceful fallback (entry_iv=None).
- Файлы: `api_example.py`, `trade_logger.py`, `database.py`.

4) **WebSocket обновления фактически не отправляются**
- Причина: `WebSocketManager` создается, но `start_broadcast_loop()` не вызывается.
- Симптом: фронтенд подключается, но не получает `portfolio_update` и прочие обновления.
- Решение: запустить broadcast loop в `lifespan`, передав `AnalysisOrchestrator` как provider.
- Файлы: `api_example.py`, `websocket_manager.py`.

5) **Несовпадение подписок WebSocket между фронтендом и backend**
- Причина: backend отправляет `options_board_update` только подписчикам `"options"`, фронтенд подписывается на `"options_board_update"`.
- Симптом: нет обновлений по доске опционов при WebSocket подключении.
- Решение: привести названия подписок к одному стандарту (например, `"options"` или `"options_board_update"`).
- Файлы: `frontend/src/services/websocket.ts`, `websocket_manager.py`.

6) **Docker Compose: frontend не видит backend**
- Причина: `VITE_API_URL=http://localhost:8000/api/v1` в контейнере указывает на самого себя, а не на сервис backend.
- Симптом: API запросы из контейнера возвращают 404/ERR_CONNECTION_REFUSED.
- Решение: заменить на `http://backend:8000/api/v1` или использовать прокси/relative URL с корректным reverse-proxy.
- Файл: `docker-compose.yml`.

7) **Docker Compose: volume override ломает прод-сборку фронтенда**
- Причина: `./frontend:/app` перекрывает `dist`, который был собран на этапе build.
- Симптом: `serve` не находит `dist`, фронтенд не поднимается.
- Решение: убрать volume для production контейнера или использовать отдельный dev Dockerfile/compose profile.
- Файл: `docker-compose.yml`, `frontend/Dockerfile`.

8) **`get_options_board` использует `_connector` без проверки**
- Причина: в `api_example.py` функция обращается к `_connector` напрямую, без проверки на None.
- Симптом: если инициализация не прошла (нет ключей, ошибка сети), endpoint упадет с 500.
- Решение: использовать dependency `get_orchestrator()` или явную проверку `_connector`.
- Файл: `api_example.py`.

9) **Исторические данные завязаны на ручной backfill**
- Причина: `iv_rank_service.py` читает из БД таблицы, но нет автоматического заполнения.
- Симптом: `/api/v1/price-history` и `/api/v1/iv-rank` возвращают пусто или 404.
- Решение: добавить cron/APS scheduler или отдельный сервис для регулярного backfill.
- Файлы: `iv_rank_service.py`, `backfill_historical_data.py`, `daily_iv_update.py`.

## 5) Отдельные замечания по запуску

- Backend и frontend не запускаются автоматически вне VS Code: требуется ручной запуск или корректная настройка Docker Compose.
- Для локальной разработки удобнее запускать backend через `startup.sh`, frontend — через `npm run dev` в `frontend/`.

