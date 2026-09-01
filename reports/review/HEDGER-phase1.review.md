# Code Review: HEDGER-phase1 (Tasks 001-005)

## Summary
- **Files reviewed**: 5
- **Issues found**: 1 Critical, 1 Warning, 2 Suggestions
- **Verdict**: **NEEDS_CHANGES**

## Critical Issues (must fix)

### Issue 1: Silent Failure in Position Monitoring
- **File**: `bybit_options/services/hedger/position_monitor.py`
- **Method**: `_get_options_delta` (lines 111-118) and `_get_futures_delta` (lines 167-174)
- **Problem**: Метод отлавливает все исключения (`Exception`) и возвращает `0.0` в качестве дельты.
- **Impact**: **Dangerous**. Если API отвалится или вернет ошибку, бот будет считать, что у него нулевая позиция.
  - Если позиция была (например, delta = +0.5), бот подумает, что она исчезла (delta = 0.0), и может попытаться "захеджировать" (на самом деле открыть новую позицию) или пропустить хеджирование реального риска.
  - Это создает риск "phantom execution" или "unhedged risk".
- **Fix**: Вместо возврата `0.0`, нужно выбрасывать кастомное исключение (например, `PositionFetchError`). Основной цикл бота (`check_and_hedge`) должен ловить это исключение и **пропускать** цикл (action: SKIP, error: "Data fetch failed"), чтобы не принимать решений на неполных данных.

## Warnings (should fix)

### Warning 1: Leaky Abstraction in OrderExecutor
- **File**: `bybit_options/services/hedger/order_executor.py`
- **Class**: `OrderExecutor` vs `ConnectorProtocol`
- **Problem**: `OrderExecutor` реализует низкоуровневую логику подписи запросов (`X-BAPI-SIGN`, headers construction) и напрямую использует `connector._session`.
  - Это нарушает инкапсуляцию `BybitConnector`.
  - Дублирует логику подписи, которая наверняка уже есть в `BybitConnector`.
  - Использует приватные атрибуты коннектора (`_session`, `_get_base_url`).
- **Suggestion**: `BybitConnector` должен предоставлять публичный метод для отправки подписанных запросов, например:
  ```python
  await connector.send_signed_request(method="POST", endpoint="/v5/order/create", payload=params)
  ```
  Или `OrderExecutor` должен использовать `connector.place_order` (если он есть), добавляя только бизнес-логику (retries, logging), но не HTTP-логику.
  *Note: Если рефакторинг коннектора сейчас невозможен, оставьте комментарий `TODO`.*

## Suggestions (nice to have)

### Suggestion 1: Config Loading Robustness
- **File**: `bybit_options/services/hedger/config.py`
- **Method**: `load_from_env`
- **Suggestion**: Добавить логирование при использовании значений по умолчанию или при ошибках парсинга. Сейчас ошибки `ValueError` глотаются молча.
  ```python
  except ValueError:
      logger.warning(f"Invalid value for {env_name}, using default: {default}")
      config_dict[field_name] = default
  ```

### Suggestion 2: Logging in Config Loader
- **File**: `bybit_options/services/hedger/config.py`
- **Suggestion**: Не хватает `logger`. Добавьте `import logging` и инициализацию логгера.

## Architecture Compliance
- [x] RiskEngine remains pure (N/A for these services)
- [x] Services handle async I/O (PositionMonitor, OrderExecutor are async)
- [x] Pydantic models on boundaries (Yes, extensively used)
- [x] Dependency injection used (Connector passed to classes)

## Security Check
- [x] No secrets in code (Secrets via env/Attributes)
- [x] Input validation present (Pydantic validators)
- [x] No SQL injection risks (asyncpg parametrized queries used)
- [ ] Rate limiting considered (Handled in OrderExecutor, but `rate_limiter` access is via private prop)

## Test Coverage
- [x] Unit tests added (Files exist: `test_position_monitor.py`, `test_order_executor.py`)
- *Note: Tests source code was not fully reviewed, but existence verified.*

---

## Next Steps
1. **Fix Critical Issue 1** in `position_monitor.py`.
2. Decide on **Warning 1** (Refactor vs TODO).
3. Proceed to **HEDGER-006** implementation.
