# AMM API Reference

## AmmEngine

### Methods

#### `initialize()`
Инициализация движка.

```python
await engine.initialize()
```

**Действия:**
1. Подключение к PostgreSQL
2. Создание BybitConnector
3. Запуск MarketDataActor
4. Загрузка активных стратегий
5. Подписка на тикеры
6. Reconciliation с биржей

---

#### `run_loop()`
Главный цикл обработки.

```python
await engine.run_loop()
```

**Частота:** 1 Hz (по умолчанию)

---

#### `run_gardener_cycle()`
Один цикл ценообразования и исполнения.

**Логика:**
1. Итерация по активным стратегиям
2. Получение Market Data (Mark IV, Mark Price)
3. Расчет Fair Price
4. Вызов `execute_leg_update()`

---

#### `execute_leg_update(strategy, leg, fair_price, iv)`
Управление ордерами для ноги.

**Параметры:**
- `strategy`: AmmStrategy
- `leg`: AmmLeg
- `fair_price`: float
- `iv`: float

**Логика:**
- Если `leg.active_order == None` → Place Order
- Иначе → Проверка отклонения → Amend Order

---

#### `stop()`
Остановка движка.

```python
await engine.stop()
```

## AmmRepository

### Methods

#### `get_active_strategies()`
Получить все активные стратегии.

```python
strategies = await repo.get_active_strategies()
```

**Returns:** `List[AmmStrategy]`

---

#### `create_strategy(strategy: AmmStrategy)`
Создать новую стратегию.

```python
strategy_id = await repo.create_strategy(strategy)
```

**Returns:** `int` (ID стратегии)

---

#### `create_leg(leg: AmmLeg)`
Добавить ногу к стратегии.

```python
leg_id = await repo.create_leg(leg)
```

**Returns:** `int` (ID ноги)

---

#### `save_order(order: AmmOrder)`
Сохранить ордер в БД.

```python
order_id = await repo.save_order(order)
```

**Returns:** `int` (ID ордера)

---

#### `update_order_status(link_id: str, status: str)`
Обновить статус ордера.

```python
await repo.update_order_status("amm-1-101-123", "FILLED")
```

## MarketDataActor

### Methods

#### `start()`
Запуск WebSocket подключения.

```python
await market_data.start()
```

---

#### `subscribe(symbols: Set[str])`
Подписка на тикеры.

```python
market_data.subscribe({"BTC-26JUN26-100000-C", "BTC-26JUN26-95000-P"})
```

---

#### `get_market_iv(symbol: str)`
Получить Mark IV.

```python
iv = market_data.get_market_iv("BTC-26JUN26-100000-C")
```

**Returns:** `Optional[float]`

---

#### `get_mark_price(symbol: str)`
Получить Mark Price.

```python
price = market_data.get_mark_price("BTC-26JUN26-100000-C")
```

**Returns:** `Optional[float]`

---

#### `get_best_bid(symbol: str)`
Получить лучший бид.

```python
bid = market_data.get_best_bid("BTC-26JUN26-100000-C")
```

**Returns:** `Optional[float]`

## OptionPricing

### Static Methods

#### `calculate_price()`
Расчет теоретической цены.

```python
price = OptionPricing.calculate_price(
    spot=100000.0,
    strike=100000.0,
    time_to_expiry=0.5,  # 6 месяцев
    risk_free_rate=0.0,
    iv=0.50,
    option_type='c'  # 'c' или 'p'
)
```

**Returns:** `float`

---

#### `calculate_greeks()`
Расчет цены и Greeks.

```python
result = OptionPricing.calculate_greeks(
    spot=100000.0,
    strike=100000.0,
    time_to_expiry=0.5,
    risk_free_rate=0.0,
    iv=0.50,
    option_type='c'
)

# result = {
#     "price": 14031.62,
#     "delta": 0.5,
#     "gamma": 0.00001,
#     "vega": 35000.0,
#     "theta": -50.0
# }
```

**Returns:** `dict`

## Models

### AmmStrategy

```python
class AmmStrategy(BaseModel):
    id: Optional[int]
    name: str
    target_iv: Decimal          # Целевая IV
    max_delta: Decimal          # Лимит дельты
    max_gamma: Decimal          # Лимит гаммы
    max_vega: Decimal           # Лимит веги
    is_active: bool
    is_paused: bool
    legs: List[AmmLeg]
```

### AmmLeg

```python
class AmmLeg(BaseModel):
    id: Optional[int]
    strategy_id: int
    symbol: str                 # BTC-26JUN26-100000-C
    side: str                   # BUY/SELL
    ratio: Decimal              # Коэффициент
    total_filled: Decimal       # Исполнено
    target_size: Decimal        # Целевой размер
    active_order: Optional[AmmOrder]
```

### AmmOrder

```python
class AmmOrder(BaseModel):
    id: Optional[int]
    leg_id: int
    bybit_order_id: str
    bybit_order_link_id: str
    price: Decimal
    iv_at_creation: Decimal
    status: str                 # NEW/ACTIVE/FILLED/CANCELLED
```

## Examples

### Полный цикл работы

```python
from bybit_options.services.amm.engine import AmmEngine
from bybit_options.services.amm.repository import AmmRepository
from bybit_options.services.amm.models import AmmStrategy, AmmLeg
from decimal import Decimal

async def main():
    # 1. Создать стратегию
    repo = AmmRepository()
    
    strategy = AmmStrategy(
        name="BTC Iron Condor",
        target_iv=Decimal("0.45"),
        max_delta=Decimal("0.5"),
        is_active=True
    )
    sid = await repo.create_strategy(strategy)
    
    # 2. Добавить ноги
    legs = [
        AmmLeg(strategy_id=sid, symbol="BTC-26JUN26-105000-C", side="SELL", ratio=Decimal("1")),
        AmmLeg(strategy_id=sid, symbol="BTC-26JUN26-110000-C", side="BUY", ratio=Decimal("1")),
        AmmLeg(strategy_id=sid, symbol="BTC-26JUN26-95000-P", side="SELL", ratio=Decimal("1")),
        AmmLeg(strategy_id=sid, symbol="BTC-26JUN26-90000-P", side="BUY", ratio=Decimal("1")),
    ]
    
    for leg in legs:
        await repo.create_leg(leg)
    
    # 3. Запустить движок
    engine = AmmEngine()
    await engine.initialize()
    await engine.run_loop()
```
