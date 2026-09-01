# Техническое Задание: Delta Hedger Bot v1.0

**Статус:** ✅ APPROVED  
**Дата:** 2026-01-16  
**Утверждено:** 2026-01-16  
**Автор:** Tech Lead (AI)  
**Приоритет:** 🔴 HIGH  

---

## 📋 Утверждённые параметры

| Параметр | Значение |
|----------|----------|
| **Telegram** | Создаём новый бот |
| **Защитные опционы (DEFENSIVE)** | Динамический размер по дельте |
| **MVP scope** | Только BTC |
| **Directional bias** | +0.01 BTC (LONG) / -0.01 BTC (SHORT) |  

---

## 1. 🎯 Цель

Создать автономного бота для управления дельтой портфеля опционов, который:
- Работает 24/7 без участия трейдера
- Реагирует на пробои ключевых фракталов
- Использует фьючерсы для микро-хеджирования
- Использует опционы для защиты при пробоях H4

---

## 2. 🏗 Архитектурный Концепт

### 2.1 Режимы работы

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DELTA HEDGER MODES                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  MODE 1: NEUTRAL (H1 внутри ключевых уровней)                           │
│    ├─ Target Delta: 0.0 BTC                                             │
│    ├─ Threshold: ±0.003 BTC                                             │
│    ├─ Instrument: Perpetual Futures (BTCUSDT)                           │
│    └─ Action: Limit orders to rebalance                                 │
│                                                                         │
│  MODE 2: DIRECTIONAL (H1 пробой ключевого фрактала)                     │
│    ├─ Target Delta: +0.01 BTC (LONG) / -0.01 BTC (SHORT)                 │
│    ├─ Threshold: ±0.003 BTC от target                                   │
│    ├─ Instrument: Perpetual Futures                                     │
│    └─ Action: Shift delta bias, maintain directional exposure           │
│                                                                         │
│  MODE 3: DEFENSIVE (H4 пробой ключевого фрактала)                       │
│    ├─ Target Delta: Depends on threat side                              │
│    ├─ Instrument: OPTIONS (buy protection near short strike)            │
│    └─ Action: Buy calls/puts to protect IC short leg                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Диаграмма потоков данных

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         DATA FLOW                                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   [Database]                    [Bybit API]                             │
│       │                              │                                  │
│       ├─ fractals_cache ────────────►│                                  │
│       ├─ bollinger_bands_history     │                                  │
│       └─ market_regime_history       │                                  │
│                                      │                                  │
│                    ┌─────────────────┴─────────────────┐                │
│                    │      DELTA HEDGER BOT             │                │
│                    │                                   │                │
│                    │  1. SignalDetector                │                │
│                    │     └─ Check H1/H4 fractal breaks │                │
│                    │                                   │                │
│                    │  2. PositionMonitor               │                │
│                    │     └─ Get current portfolio delta│                │
│                    │                                   │                │
│                    │  3. ModeController                │                │
│                    │     └─ NEUTRAL / DIRECTIONAL /    │                │
│                    │        DEFENSIVE                  │                │
│                    │                                   │                │
│                    │  4. OrderExecutor                 │                │
│                    │     └─ Place limit orders         │                │
│                    │                                   │
│                    └─────────────────┬─────────────────┘                │
│                                      │                                  │
│                                      ▼                                  │
│                              [Bybit Orders]                             │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Используемые библиотеки

| Библиотека | Назначение |
|------------|------------|
| `pybit` | Bybit API (REST + WebSocket) |
| `asyncio` | Асинхронное выполнение |
| `asyncpg` | PostgreSQL async driver |
| `pydantic` | Модели данных и валидация |
| `apscheduler` | Планировщик задач (проверка каждые N минут) |
| `structlog` | Структурированное логирование |

---

## 3. 💾 Схема Базы Данных

### 3.1 Новые таблицы

```sql
-- Логирование действий хеджера
CREATE TABLE IF NOT EXISTS hedge_actions (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Контекст
    mode VARCHAR(20) NOT NULL,  -- 'NEUTRAL', 'DIRECTIONAL', 'DEFENSIVE'
    trigger_source VARCHAR(20), -- 'H1_FRACTAL', 'H4_FRACTAL', 'THRESHOLD', 'MANUAL'
    fractal_price DECIMAL(12, 2),
    fractal_timeframe VARCHAR(3),
    
    -- Позиция до действия
    delta_before DECIMAL(18, 8) NOT NULL,
    target_delta DECIMAL(18, 8) NOT NULL,
    
    -- Действие
    action_type VARCHAR(20) NOT NULL,  -- 'FUTURES_HEDGE', 'OPTIONS_BUY', 'SKIP'
    instrument VARCHAR(50),
    side VARCHAR(10),  -- 'BUY', 'SELL'
    size DECIMAL(18, 8),
    order_type VARCHAR(20),  -- 'LIMIT', 'MARKET'
    limit_price DECIMAL(18, 8),
    
    -- Результат
    order_id VARCHAR(100),
    exec_price DECIMAL(18, 8),
    delta_after DECIMAL(18, 8),
    status VARCHAR(20) NOT NULL,  -- 'PLACED', 'FILLED', 'CANCELLED', 'FAILED'
    error_message TEXT,
    
    -- Метаданные
    execution_time_ms INT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_hedge_actions_time ON hedge_actions(timestamp DESC);
CREATE INDEX idx_hedge_actions_mode ON hedge_actions(mode, timestamp DESC);
CREATE INDEX idx_hedge_actions_status ON hedge_actions(status);

-- Конфигурация хеджера
CREATE TABLE IF NOT EXISTS hedger_config (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Начальные значения конфигурации
INSERT INTO hedger_config (key, value, description) VALUES
('mode', 'NEUTRAL', 'Current operating mode'),
('target_delta', '0.0', 'Target delta in BTC'),
('threshold', '0.003', 'Rebalance threshold in BTC'),
('directional_bias', '0.0', 'Delta bias for DIRECTIONAL mode'),
('enabled', 'false', 'Is bot enabled'),
('check_interval_seconds', '60', 'How often to check delta'),
('max_order_size', '0.1', 'Max single order size in BTC'),
('limit_price_offset_bps', '5', 'Limit price offset in basis points')
ON CONFLICT (key) DO NOTHING;

COMMENT ON TABLE hedge_actions IS 'Log of all hedging actions taken by Delta Hedger Bot';
COMMENT ON TABLE hedger_config IS 'Runtime configuration for Delta Hedger Bot';
```

### 3.2 Обоснование типов данных

| Поле | Тип | Почему |
|------|-----|--------|
| `delta_*` | `DECIMAL(18, 8)` | Точность до 8 знаков (satoshi-level) |
| `mode` | `VARCHAR(20)` | Enum-like, но гибкий для расширения |
| `limit_price` | `DECIMAL(18, 8)` | Совместимость с Bybit price precision |
| `execution_time_ms` | `INT` | Для мониторинга latency |

---

## 4. 🛠 User Stories & Pseudo-Code

### 4.1 Основные компоненты

#### 4.1.1 DeltaHedgerBot (главный класс)

```python
class DeltaHedgerBot:
    """
    Главный контроллер Delta Hedger Bot.
    
    Responsibilities:
    - Периодическая проверка дельты
    - Определение текущего режима
    - Запуск хеджирования при необходимости
    """
    
    def __init__(
        self,
        connector: BybitConnector,
        db_pool: asyncpg.Pool,
        config: HedgerConfig
    ):
        self.connector = connector
        self.db = db_pool
        self.config = config
        self.signal_detector = SignalDetector(db_pool)
        self.position_monitor = PositionMonitor(connector)
        self.order_executor = OrderExecutor(connector)
        self.mode = HedgerMode.NEUTRAL
        self.is_running = False
    
    async def start(self):
        """Запуск бота в бесконечном цикле."""
        self.is_running = True
        logger.info("Delta Hedger Bot started", mode=self.mode.value)
        
        while self.is_running:
            try:
                await self.check_and_hedge()
            except Exception as e:
                logger.error("Hedge cycle failed", error=str(e))
            
            await asyncio.sleep(self.config.check_interval_seconds)
    
    async def stop(self):
        """Остановка бота."""
        self.is_running = False
        logger.info("Delta Hedger Bot stopped")
    
    async def check_and_hedge(self):
        """Основной цикл проверки и хеджирования."""
        # 1. Проверяем сигналы (пробои фракталов)
        signal = await self.signal_detector.detect()
        
        # 2. Обновляем режим на основе сигнала
        new_mode = self._determine_mode(signal)
        if new_mode != self.mode:
            await self._switch_mode(new_mode, signal)
        
        # 3. Получаем текущую дельту
        current_delta = await self.position_monitor.get_portfolio_delta()
        
        # 4. Вычисляем целевую дельту
        target_delta = self._calculate_target_delta()
        
        # 5. Проверяем необходимость хеджирования
        deviation = abs(current_delta - target_delta)
        if deviation > self.config.threshold:
            await self._execute_hedge(current_delta, target_delta, signal)
    
    def _determine_mode(self, signal: Optional[FractalSignal]) -> HedgerMode:
        """Определяет режим на основе сигнала."""
        if signal is None:
            return HedgerMode.NEUTRAL
        
        if signal.timeframe == "H4" and signal.is_breakout:
            return HedgerMode.DEFENSIVE
        elif signal.timeframe == "H1" and signal.is_breakout:
            return HedgerMode.DIRECTIONAL
        else:
            return HedgerMode.NEUTRAL
    
    def _calculate_target_delta(self) -> float:
        """Вычисляет целевую дельту для текущего режима."""
        if self.mode == HedgerMode.NEUTRAL:
            return 0.0
        elif self.mode == HedgerMode.DIRECTIONAL:
            return self.config.directional_bias  # Positive for long, negative for short
        elif self.mode == HedgerMode.DEFENSIVE:
            return 0.0  # Return to neutral during defense
        return 0.0
    
    async def _switch_mode(self, new_mode: HedgerMode, signal: Optional[FractalSignal]):
        """Переключение режима с логированием."""
        old_mode = self.mode
        self.mode = new_mode
        logger.info(
            "Mode switched",
            old_mode=old_mode.value,
            new_mode=new_mode.value,
            signal=signal
        )
        
        # Если переходим в DEFENSIVE — покупаем защитные опционы
        if new_mode == HedgerMode.DEFENSIVE and signal:
            await self._buy_protection_options(signal)
    
    async def _execute_hedge(
        self,
        current_delta: float,
        target_delta: float,
        signal: Optional[FractalSignal]
    ):
        """Выполняет хеджирование фьючерсами."""
        hedge_size = target_delta - current_delta
        side = "BUY" if hedge_size > 0 else "SELL"
        size = min(abs(hedge_size), self.config.max_order_size)
        
        # Вычисляем лимитную цену
        ticker = await self.connector.get_ticker("BTCUSDT")
        offset_bps = self.config.limit_price_offset_bps / 10000
        if side == "BUY":
            limit_price = ticker.bid * (1 + offset_bps)
        else:
            limit_price = ticker.ask * (1 - offset_bps)
        
        # Размещаем ордер
        order = await self.order_executor.place_limit_order(
            symbol="BTCUSDT",
            side=side,
            size=size,
            price=limit_price
        )
        
        # Логируем действие
        await self._log_action(
            mode=self.mode,
            trigger_source=signal.timeframe if signal else "THRESHOLD",
            delta_before=current_delta,
            target_delta=target_delta,
            action_type="FUTURES_HEDGE",
            instrument="BTCUSDT",
            side=side,
            size=size,
            order_type="LIMIT",
            limit_price=limit_price,
            order_id=order.order_id,
            status="PLACED"
        )
    
    async def _buy_protection_options(self, signal: FractalSignal):
        """
        Покупает защитные опционы при пробое H4.
        
        Логика:
        - Если пробой вверх (цена > фрактал) — покупаем CALL перед short call strike
        - Если пробой вниз (цена < фрактал) — покупаем PUT перед short put strike
        """
        # TODO: Implement in Phase 2
        # 1. Определить направление пробоя
        # 2. Найти short strike текущего IC
        # 3. Выбрать опцион для покупки (ближайший strike к short leg)
        # 4. Рассчитать размер (частичное покрытие)
        # 5. Разместить ордер
        logger.info(
            "Protection options buy triggered",
            signal=signal,
            note="Implementation pending in Phase 2"
        )
```

#### 4.1.2 SignalDetector (детектор сигналов)

```python
class SignalDetector:
    """
    Детектор пробоев ключевых фракталов.
    
    Читает данные из БД:
    - fractals_cache (ключевые фракталы H1/H4)
    - perpetual_ohlcv (текущая цена)
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db = db_pool
    
    async def detect(self) -> Optional[FractalSignal]:
        """
        Проверяет пробои на H1 и H4.
        
        Returns:
            FractalSignal если есть пробой, None если нет
        """
        # 1. Получаем текущую цену
        current_price = await self._get_current_price()
        
        # 2. Проверяем H4 сначала (более приоритетный)
        h4_signal = await self._check_fractal_breakout("H4", current_price)
        if h4_signal:
            return h4_signal
        
        # 3. Проверяем H1
        h1_signal = await self._check_fractal_breakout("H1", current_price)
        if h1_signal:
            return h1_signal
        
        return None
    
    async def _check_fractal_breakout(
        self,
        timeframe: str,
        current_price: float
    ) -> Optional[FractalSignal]:
        """
        Проверяет пробой ключевого фрактала.
        
        Условия:
        - Фрактал помечен как is_key_fractal = TRUE
        - Цена закрылась за уровнем фрактала
        """
        query = """
            SELECT 
                timestamp,
                price,
                type  -- 'HIGH' or 'LOW'
            FROM fractals_cache
            WHERE timeframe = $1
              AND base_coin = 'BTC'
              AND is_key_fractal = TRUE
            ORDER BY timestamp DESC
            LIMIT 2  -- Последние support и resistance
        """
        
        rows = await self.db.fetch(query, timeframe)
        
        for row in rows:
            fractal_price = float(row['price'])
            fractal_type = row['type']
            
            # Пробой вверх (цена > resistance fractal)
            if fractal_type == 'HIGH' and current_price > fractal_price:
                return FractalSignal(
                    timeframe=timeframe,
                    fractal_type=fractal_type,
                    fractal_price=fractal_price,
                    current_price=current_price,
                    direction="LONG",
                    is_breakout=True
                )
            
            # Пробой вниз (цена < support fractal)
            if fractal_type == 'LOW' and current_price < fractal_price:
                return FractalSignal(
                    timeframe=timeframe,
                    fractal_type=fractal_type,
                    fractal_price=fractal_price,
                    current_price=current_price,
                    direction="SHORT",
                    is_breakout=True
                )
        
        return None
    
    async def _get_current_price(self) -> float:
        """Получает последнюю цену закрытия."""
        query = """
            SELECT close
            FROM perpetual_ohlcv
            WHERE symbol = 'BTCUSDT'
            ORDER BY timestamp DESC
            LIMIT 1
        """
        row = await self.db.fetchrow(query)
        return float(row['close'])
```

#### 4.1.3 PositionMonitor (мониторинг позиций)

```python
class PositionMonitor:
    """
    Мониторинг текущей дельты портфеля.
    
    Агрегирует:
    - Options positions (from Bybit API)
    - Futures positions (from Bybit API)
    """
    
    def __init__(self, connector: BybitConnector):
        self.connector = connector
    
    async def get_portfolio_delta(self) -> float:
        """
        Возвращает общую дельту портфеля в BTC.
        
        Formula:
        Total Delta = Σ(option_delta * size) + futures_position
        """
        # 1. Получаем опционные позиции
        options = await self.connector.get_positions(category="option")
        options_delta = sum(
            float(pos.delta) * float(pos.size)
            for pos in options
            if pos.delta is not None
        )
        
        # 2. Получаем фьючерсную позицию
        futures = await self.connector.get_positions(category="linear")
        futures_delta = sum(
            float(pos.size) * (1 if pos.side == "Buy" else -1)
            for pos in futures
            if pos.symbol == "BTCUSDT"
        )
        
        total_delta = options_delta + futures_delta
        
        logger.debug(
            "Portfolio delta calculated",
            options_delta=options_delta,
            futures_delta=futures_delta,
            total_delta=total_delta
        )
        
        return total_delta
```

#### 4.1.4 OrderExecutor (исполнение ордеров)

```python
class OrderExecutor:
    """
    Исполнение ордеров через Bybit API.
    
    Features:
    - Limit orders only (по требованию)
    - Retry logic с exponential backoff
    - Логирование всех операций
    """
    
    def __init__(self, connector: BybitConnector):
        self.connector = connector
        self.max_retries = 3
        self.base_delay = 1.0  # seconds
    
    async def place_limit_order(
        self,
        symbol: str,
        side: str,
        size: float,
        price: float
    ) -> OrderResult:
        """
        Размещает лимитный ордер с retry логикой.
        
        Args:
            symbol: Trading pair (e.g., "BTCUSDT")
            side: "BUY" or "SELL"
            size: Order size in base currency
            price: Limit price
            
        Returns:
            OrderResult with order_id and status
        """
        for attempt in range(self.max_retries):
            try:
                result = await self.connector.place_order(
                    category="linear",
                    symbol=symbol,
                    side=side,
                    orderType="Limit",
                    qty=str(size),
                    price=str(price),
                    timeInForce="GTC"  # Good Till Cancel
                )
                
                return OrderResult(
                    order_id=result['orderId'],
                    status="PLACED",
                    price=price,
                    size=size
                )
                
            except RateLimitError:
                delay = self.base_delay * (2 ** attempt)
                logger.warning(f"Rate limited, waiting {delay}s")
                await asyncio.sleep(delay)
                
            except APIError as e:
                logger.error(f"API error: {e}")
                if attempt == self.max_retries - 1:
                    return OrderResult(
                        order_id=None,
                        status="FAILED",
                        error=str(e)
                    )
        
        return OrderResult(order_id=None, status="FAILED", error="Max retries exceeded")
```

### 4.2 Pydantic Models

```python
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class HedgerMode(str, Enum):
    NEUTRAL = "NEUTRAL"
    DIRECTIONAL = "DIRECTIONAL"
    DEFENSIVE = "DEFENSIVE"

class HedgerConfig(BaseModel):
    """Конфигурация Delta Hedger Bot."""
    mode: HedgerMode = HedgerMode.NEUTRAL
    target_delta: float = 0.0
    threshold: float = 0.003  # BTC
    directional_bias: float = 0.0  # For DIRECTIONAL mode
    enabled: bool = False
    check_interval_seconds: int = 60
    max_order_size: float = 0.1  # BTC
    limit_price_offset_bps: int = 5  # Basis points

class FractalSignal(BaseModel):
    """Сигнал пробоя фрактала."""
    timeframe: str  # "H1" or "H4"
    fractal_type: str  # "HIGH" or "LOW"
    fractal_price: float
    current_price: float
    direction: str  # "LONG" or "SHORT"
    is_breakout: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class OrderResult(BaseModel):
    """Результат размещения ордера."""
    order_id: Optional[str]
    status: str  # "PLACED", "FILLED", "FAILED"
    price: Optional[float] = None
    size: Optional[float] = None
    error: Optional[str] = None

class HedgeAction(BaseModel):
    """Запись действия хеджера для логирования."""
    mode: HedgerMode
    trigger_source: str
    fractal_price: Optional[float] = None
    fractal_timeframe: Optional[str] = None
    delta_before: float
    target_delta: float
    action_type: str
    instrument: str
    side: str
    size: float
    order_type: str
    limit_price: float
    order_id: Optional[str] = None
    exec_price: Optional[float] = None
    delta_after: Optional[float] = None
    status: str
    error_message: Optional[str] = None
```

---

## 5. 🛡 Edge Cases & Risk Management

### 5.1 Критические сценарии

| Сценарий | Что делать | Реализация |
|----------|------------|------------|
| **Интернет отвалился** | Retry + алерт | Exponential backoff, Telegram notification |
| **Bybit API 502/503** | Retry + fallback | Max 3 retries, wait before next cycle |
| **Ордер не исполнился** | Cancel + retry с новой ценой | Order status check, re-quote |
| **Delta слишком большая** | Emergency hedge | If \|delta\| > 0.5 BTC → force hedge |
| **Нет ликвидности** | Уменьшить размер ордера | Dynamic size based on orderbook |
| **Conflicting signals** | H4 > H1 priority | H4 breakout overrides H1 |
| **Bot restart** | Resume from DB state | Load last mode from hedger_config |

### 5.2 Валидация входных данных

```python
def validate_hedge_action(
    current_delta: float,
    target_delta: float,
    size: float,
    config: HedgerConfig
) -> tuple[bool, str]:
    """
    Валидирует параметры хеджирования.
    
    Returns:
        (is_valid, error_message)
    """
    # 1. Размер не больше максимального
    if size > config.max_order_size:
        return False, f"Size {size} exceeds max {config.max_order_size}"
    
    # 2. Дельта в разумных пределах
    if abs(target_delta) > 1.0:  # 1 BTC max
        return False, f"Target delta {target_delta} too large"
    
    # 3. Deviation достаточно большая
    deviation = abs(current_delta - target_delta)
    if deviation < config.threshold:
        return False, f"Deviation {deviation} below threshold {config.threshold}"
    
    return True, ""
```

### 5.3 Логирование и алерты

```python
# Уровни алертов
ALERT_LEVELS = {
    "INFO": ["mode_switch", "hedge_executed"],
    "WARNING": ["order_retry", "high_delta"],
    "ERROR": ["order_failed", "api_error"],
    "CRITICAL": ["emergency_hedge", "position_risk"]
}

# Telegram notification (optional)
async def send_alert(level: str, message: str, context: dict):
    if level in ["ERROR", "CRITICAL"]:
        await telegram_bot.send_message(
            chat_id=ALERT_CHAT_ID,
            text=f"🚨 {level}: {message}\n\nContext: {json.dumps(context, indent=2)}"
        )
```

---

## 6. 📁 Структура файлов

```
bybit_options/
├── services/
│   └── hedger/
│       ├── __init__.py
│       ├── bot.py              # DeltaHedgerBot main class
│       ├── signal_detector.py  # SignalDetector
│       ├── position_monitor.py # PositionMonitor
│       ├── order_executor.py   # OrderExecutor
│       ├── models.py           # Pydantic models
│       └── config.py           # HedgerConfig loader
├── scripts/
│   └── run_hedger.py           # Entry point script
└── tests/
    └── test_hedger/
        ├── test_signal_detector.py
        ├── test_position_monitor.py
        └── test_order_executor.py
```

---

## 7. 📅 План реализации

### Phase 1: Core (MVP)
**Срок: 3-5 дней**

- [ ] Создать структуру директорий
- [ ] Реализовать `models.py` (Pydantic models)
- [ ] Реализовать `position_monitor.py` (get_portfolio_delta)
- [ ] Реализовать `order_executor.py` (place_limit_order)
- [ ] Реализовать `bot.py` NEUTRAL mode only
- [ ] Добавить SQL миграции
- [ ] Базовые unit-тесты

### Phase 2: Signal Detection
**Срок: 2-3 дня**

- [ ] Реализовать `signal_detector.py`
- [ ] Интеграция с fractals_cache
- [ ] DIRECTIONAL mode (H1 breakout)
- [ ] Тесты на исторических данных

### Phase 3: Defensive Mode
**Срок: 3-4 дня**

- [ ] DEFENSIVE mode (H4 breakout)
- [ ] Логика покупки защитных опционов
- [ ] Интеграция с текущими позициями IC
- [ ] Тесты сценариев защиты

### Phase 4: Production Ready
**Срок: 2-3 дня**

- [ ] Telegram alerts
- [ ] Graceful shutdown
- [ ] Docker/systemd deployment
- [ ] Мониторинг и dashboard
- [ ] Документация

---

## 8. ✅ Acceptance Criteria

### AC1: Bot starts and runs continuously
```bash
python scripts/run_hedger.py
# Logs: "Delta Hedger Bot started, mode=NEUTRAL"
# Checks delta every 60 seconds
```

### AC2: Neutral mode hedging works
```
Given: portfolio delta = +0.05 BTC, threshold = 0.003
When: bot checks delta
Then: places SELL order for 0.05 BTC BTCUSDT futures
```

### AC3: H1 breakout triggers directional mode
```
Given: H1 key fractal at 95000
When: price closes above 95000
Then: mode switches to DIRECTIONAL, bias = +0.01 BTC
```

### AC4: H4 breakout triggers defensive mode
```
Given: H4 key fractal at 90000, IC short put at 88000
When: price closes below 90000
Then: mode switches to DEFENSIVE, buys PUT near 88000
```

### AC5: Orders are logged to database
```sql
SELECT * FROM hedge_actions ORDER BY timestamp DESC LIMIT 1;
-- Returns last hedge action with all details
```

---

## 9. 🔗 Зависимости от существующего кода

| Модуль | Используется для |
|--------|------------------|
| `BybitConnector` | API calls |
| `fractals_cache` table | Signal detection |
| `perpetual_ohlcv` table | Current price |
| `position_entries` table | Optional: current IC positions |
| `delta_models.py` | Optional: extend with hedger models |

---

## 10. ✅ Решённые вопросы

| Вопрос | Решение |
|--------|---------|
| **Telegram alerts** | ✅ Создаём новый бот |
| **Options buying logic (DEFENSIVE)** | ✅ Динамический размер по дельте |
| **Multi-asset** | ✅ MVP только BTC |
| **Directional bias** | ✅ +0.01 BTC (LONG) / -0.01 BTC (SHORT) |

---

## 11. 📝 Логика покупки защитных опционов (DEFENSIVE mode)

### Динамический расчёт размера по дельте

```python
async def _buy_protection_options(self, signal: FractalSignal):
    """
    Покупает защитные опционы при пробое H4.
    
    Размер = текущая дельта экспозиции к угрожаемому краю.
    
    Логика:
    1. Определить направление пробоя
    2. Найти short strike текущего IC
    3. Рассчитать дельту short leg (угроза)
    4. Купить опцион с размером = abs(short_leg_delta)
    """
    # 1. Определяем какой край под угрозой
    if signal.direction == "SHORT":
        # Цена падает → short put под угрозой
        threat_side = "PUT"
    else:
        # Цена растёт → short call под угрозой
        threat_side = "CALL"
    
    # 2. Получаем текущие опционные позиции
    positions = await self.connector.get_positions(category="option")
    
    # 3. Находим short leg под угрозой
    short_leg = None
    for pos in positions:
        is_short = float(pos.size) < 0
        is_target_type = threat_side in pos.symbol
        if is_short and is_target_type:
            short_leg = pos
            break
    
    if not short_leg:
        logger.warning("No short leg found for protection")
        return
    
    # 4. Рассчитываем размер защитного опциона
    # Размер = дельта short leg (чтобы нейтрализовать риск)
    protection_delta = abs(float(short_leg.delta) * float(short_leg.size))
    
    # 5. Ищем ATM или near-ATM опцион для покупки
    # Ближайший страйк к текущей цене
    strike = self._find_nearest_strike(signal.current_price, threat_side)
    
    # 6. Рассчитываем количество контрактов
    # option_delta ≈ 0.5 для ATM, поэтому:
    protection_size = protection_delta / 0.5  # Примерный расчёт
    protection_size = min(protection_size, self.config.max_option_size)
    
    # 7. Размещаем ордер
    symbol = f"BTC-{expiry}-{int(strike)}-{threat_side[0]}"
    
    order = await self.order_executor.place_option_order(
        symbol=symbol,
        side="BUY",
        size=protection_size
    )
    
    logger.info(
        "Protection option bought",
        symbol=symbol,
        size=protection_size,
        protection_delta=protection_delta,
        signal=signal
    )
```

---

**Следующий шаг:** Декомпозиция на Task Cards → передача AI-кодеру (Implementer).

