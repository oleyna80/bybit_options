"""
Delta Hedger Bot - Pydantic Models

Модели данных для Delta Hedger Bot:
- HedgerMode: Режимы работы бота
- HedgerConfig: Конфигурация бота
- FractalSignal: Сигнал пробоя фрактала
- OrderResult: Результат размещения ордера
- HedgeAction: Запись действия для логирования
"""

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class HedgerMode(str, Enum):
    """Режимы работы Delta Hedger Bot."""
    
    NEUTRAL = "NEUTRAL"          # Дельта = 0, микро-хеджирование фьючерсами
    DIRECTIONAL = "DIRECTIONAL"  # Дельта смещена в сторону тренда (H1 breakout)
    DEFENSIVE = "DEFENSIVE"      # Защитный режим, покупка опционов (H4 breakout)


class HedgerConfig(BaseModel):
    """
    Конфигурация Delta Hedger Bot.
    
    Attributes:
        mode: Текущий режим работы
        target_delta: Целевая дельта портфеля в BTC
        threshold: Порог для ребалансировки в BTC
        directional_bias_long: Смещение дельты для LONG направления
        directional_bias_short: Смещение дельты для SHORT направления
        enabled: Включен ли бот
        check_interval_seconds: Интервал проверки в секундах
        max_order_size: Максимальный размер одного ордера в BTC
        limit_price_offset_bps: Смещение лимитной цены в базисных пунктах
        max_option_size: Максимальный размер опционного ордера
    """
    
    mode: HedgerMode = HedgerMode.NEUTRAL
    target_delta: float = 0.0
    threshold: float = 0.003  # BTC
    directional_bias_long: float = 0.01   # +0.01 BTC for LONG
    directional_bias_short: float = -0.01  # -0.01 BTC for SHORT
    enabled: bool = False
    check_interval_seconds: int = 60
    max_order_size: float = 0.1  # BTC
    limit_price_offset_bps: int = 5  # Basis points (0.05%)
    max_option_size: float = 0.5  # Max option contracts to buy
    
    # Defensive Mode Config
    option_price_markup_pct: float = 5.0  # Markup over best ask (%)
    hedge_base_coin: str = "BTC"  # Base coin for hedging
    
    @field_validator('threshold', 'max_order_size', 'option_price_markup_pct')
    @classmethod
    def must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError('must be positive')
        return v
    
    @field_validator('check_interval_seconds')
    @classmethod
    def min_interval(cls, v: int) -> int:
        if v < 10:
            raise ValueError('check_interval_seconds must be at least 10')
        return v
    
    model_config = {
        "frozen": False,  # Allow mutation for runtime updates
        "extra": "ignore"
    }


class FractalSignal(BaseModel):
    """
    Сигнал пробоя ключевого фрактала.
    
    Генерируется SignalDetector при обнаружении пробоя
    ключевого фрактала на H1 или H4.
    
    Attributes:
        timeframe: Таймфрейм сигнала ("H1" или "H4")
        fractal_type: Тип фрактала ("HIGH" или "LOW")
        fractal_price: Цена фрактала
        current_price: Текущая цена при обнаружении
        direction: Направление пробоя ("LONG" или "SHORT")
        is_breakout: Флаг подтверждённого пробоя
        timestamp: Время генерации сигнала
    """
    
    timeframe: str = Field(..., pattern=r'^(H1|H4|D1)$')
    fractal_type: str = Field(..., pattern=r'^(HIGH|LOW)$')
    fractal_price: float = Field(..., gt=0)
    current_price: float = Field(..., gt=0)
    direction: str = Field(..., pattern=r'^(LONG|SHORT)$')
    is_breakout: bool = True
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @property
    def is_bullish(self) -> bool:
        """True если сигнал бычий (пробой вверх)."""
        return self.direction == "LONG"
    
    @property
    def is_bearish(self) -> bool:
        """True если сигнал медвежий (пробой вниз)."""
        return self.direction == "SHORT"
    
    model_config = {
        "frozen": True  # Immutable after creation
    }


class OrderResult(BaseModel):
    """
    Результат размещения ордера.
    
    Возвращается OrderExecutor после попытки размещения ордера.
    
    Attributes:
        order_id: ID ордера на бирже (None если failed)
        status: Статус ордера
        symbol: Торговый символ
        side: Сторона сделки
        price: Цена исполнения
        size: Размер ордера
        error: Сообщение об ошибке (если failed)
        execution_time_ms: Время выполнения в миллисекундах
    """
    
    order_id: Optional[str] = None
    status: str = Field(..., pattern=r'^(PLACED|FILLED|CANCELLED|FAILED|PENDING)$')
    symbol: Optional[str] = None
    side: Optional[str] = None
    price: Optional[float] = None
    size: Optional[float] = None
    error: Optional[str] = None
    execution_time_ms: Optional[int] = None
    
    @property
    def is_success(self) -> bool:
        """True если ордер успешно размещён или исполнен."""
        return self.status in ("PLACED", "FILLED")
    
    @property
    def is_failed(self) -> bool:
        """True если ордер не удался."""
        return self.status == "FAILED"
    
    model_config = {
        "frozen": True
    }


class HedgeAction(BaseModel):
    """
    Запись действия хеджера для логирования в БД.
    
    Каждое действие (хедж/пропуск) записывается в таблицу hedge_actions.
    
    Attributes:
        mode: Режим работы бота
        trigger_source: Источник триггера
        fractal_price: Цена фрактала (если применимо)
        fractal_timeframe: Таймфрейм фрактала (если применимо)
        delta_before: Дельта до действия
        target_delta: Целевая дельта
        action_type: Тип действия
        instrument: Торговый инструмент
        side: Сторона сделки
        size: Размер сделки
        order_type: Тип ордера
        limit_price: Лимитная цена
        order_id: ID ордера (если размещён)
        exec_price: Цена исполнения
        delta_after: Дельта после действия
        status: Статус действия
        error_message: Сообщение об ошибке
        timestamp: Время действия
    """
    
    mode: HedgerMode
    trigger_source: str = Field(
        ..., 
        pattern=r'^(H1_FRACTAL|H4_FRACTAL|THRESHOLD|MANUAL|EMERGENCY|MODE_SWITCH)$'
    )
    fractal_price: Optional[float] = None
    fractal_timeframe: Optional[str] = None
    delta_before: float
    target_delta: float
    action_type: str = Field(
        ..., 
        pattern=r'^(FUTURES_HEDGE|OPTIONS_BUY|OPTIONS_CLOSE|SKIP|EMERGENCY)$'
    )
    instrument: str
    side: str = Field(..., pattern=r'^(BUY|SELL)$')
    size: float = Field(..., ge=0)
    order_type: str = Field(..., pattern=r'^(LIMIT|MARKET)$')
    limit_price: float = Field(..., gt=0)
    order_id: Optional[str] = None
    exec_price: Optional[float] = None
    delta_after: Optional[float] = None
    status: str = Field(..., pattern=r'^(PLACED|FILLED|CANCELLED|FAILED|SKIPPED)$')
    error_message: Optional[str] = None
    execution_time_ms: Optional[int] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @property
    def deviation(self) -> float:
        """Отклонение от целевой дельты до действия."""
        return abs(self.delta_before - self.target_delta)
    
    model_config = {
        "frozen": True
    }


# Type aliases for convenience
DeltaBTC = float  # Delta in BTC units
PriceBTC = float  # Price in BTC
SizeBTC = float   # Size in BTC
