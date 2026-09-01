# Conventions (Bybit Options Risk Engine)

Правила для ИИ-агентов: как понимать проект, писать код и двигать задачи.

## Общая информация
- Назначение: async-сервис для анализа опционного портфеля Bybit (Greeks, риск-метрики, Markdown-отчеты, API для фронтенда).
- **Production entrypoints:** `bybit_options/api/app.py` (FastAPI), `scripts/run_hedger.py` (Delta Hedger).
- **Demo/Legacy entrypoints:** `main.py` (CLI demo), `api_example.py` (FastAPI demo).
- Отчеты: сохраняются в `reports/` (timestamp + `latest_analysis.md`).
- **Runtime SSOT:** См. [`docs/ops/running.md`](../docs/ops/running.md) для портов, команд и env vars.

## Технологический стек
- Backend: Python 3.10+ (asyncio, aiohttp, pydantic), FastAPI (пример), uvicorn.
- Frontend: React (Vite) в каталоге `frontend/`, подключается к API через `VITE_API_URL` (по умолчанию `/api/v1`, проксируется Vite на `http://localhost:8000`). См. [`docs/ops/running.md`](../docs/ops/running.md).
- Хранилища/инфра (план/опционально): Redis (кэш), PostgreSQL (история), Docker/Docker Compose.
- Форматы: JSON ответы API, Markdown отчеты.

## Архитектурные принципы
- Разделение ответственностей: `BybitConnector` (HTTP/подписи/лимитер), `MarketDataService` (фетч + кэш), `RiskEngine` (чистая логика, без I/O), `AnalysisOrchestrator` (workflow), `DisplayManager` (презентация/Markdown).
- Async-first: весь I/O через `async/await`; параллельные фетчи через `asyncio.gather`.
- Типобезопасность: Pydantic-модели для всех входов/выходов.
- Детеминированность: `RiskEngine` без побочных эффектов, одинаковый ввод → одинаковый вывод.
- Dependency injection: коннекторы/сервисы передаются извне, не создаются внутри.

## Правила написания кода
- Кодировка UTF-8; логика на английском, комментарии краткие и по делу.
- Не размещать I/O в бизнес-логике (`RiskEngine` должен оставаться чистым).
- Использовать Pydantic модели вместо «dict» для публичных API/функций.
- Для опционных расчетов соблюдать знаки Greeks: шорт инвертирует все греки; CALL δ>0, PUT δ<0; gamma/vega ≥0 до применения позиции.
- Обрабатывать пагинацию и rate limit защитно (см. `BybitConnector` — токен-бакет, проверка cursor).
- Кэш тикеров/инструментов использовать из `MarketDataService`, не дублировать.
- Логи: через `logging` (уровень из `LOG_LEVEL`), избегать утечек ключей/секретов.
- CLI/скрипты: читать ключи из `.env` (`BYBIT_API_KEY`, `BYBIT_API_SECRET`), валидировать наличие, печатать дружелюбные ошибки.

## Безопасность
- Никогда не коммитить `.env`; секреты только в переменных окружения.
- HTTPS к Bybit, не логировать подписи/секреты/полные запросы.
- В FastAPI включать CORS/авторизацию перед продом; ограничивать rate limit на выходе, уважать лимиты Bybit.
- Проверять входные параметры API через Pydantic; не доверять пользовательскому вводу.
- Отчеты/логи не должны содержать приватные ключи, только агрегированные метрики.

## Тестирование
- Юнит-тесты: `RiskEngine` и вспомогательные утилиты (чистые функции, проверки знаков греков, IV diff, gamma rent).
- Интеграционные: `MarketDataService` и `AnalysisOrchestrator` с моками коннектора; сценарии без позиций, ошибки API, сломанные курсоры.
- E2E (опционально): против testnet Bybit с настоящими ключами (отдельное окружение).
- При добавлении фич: покрывать негативные кейсы (0-size позы, пустые тикеры, iv=0, spreads=0).

## Процесс разработки
- Окружение: `python -m venv .venv && pip install -r requirements.txt`; фронт — `npm install` в `frontend/`.
- **Запуск:** См. [`docs/ops/running.md`](../docs/ops/running.md) для актуальных портов и команд.
- Репорты: убедиться, что `reports/` существует/доступна на запись.
- Изменения в логике: новые расчеты — в `RiskEngine`; новые фетчи/кэш — в `MarketDataService`; новые пайплайны — в `AnalysisOrchestrator`.
- Pull-request чеклист: линт/формат (pep8/ruff при наличии), тесты по затронутым слоям, обновить релевантные MD (readme/guide/usage) и, при необходимости, пример в `INTEGRATION.md`.

