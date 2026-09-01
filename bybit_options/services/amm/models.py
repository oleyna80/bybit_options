from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

# --- Enums ---
class AmmStatus:
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"

class OrderStatus:
    NEW = "NEW"
    ACTIVE = "ACTIVE"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"

# --- Models ---

class AmmOrder(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: Optional[int] = None
    leg_id: int
    bybit_order_id: Optional[str] = None
    bybit_order_link_id: str
    price: Decimal
    iv_at_creation: Optional[Decimal] = None
    status: str = OrderStatus.NEW
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class AmmLeg(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: Optional[int] = None
    strategy_id: Optional[int] = None
    symbol: str
    side: str  # BUY / SELL
    ratio: Decimal = Decimal("1.0")
    is_active: bool = True
    total_filled: Decimal = Decimal("0")
    target_size: Decimal = Decimal("0")
    
    # Runtime state (not in DB usually, or joined)
    active_order: Optional[AmmOrder] = None

class AmmStrategy(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: Optional[int] = None
    name: str
    sub_account_id: Optional[str] = None
    
    is_active: bool = False
    is_paused: bool = False
    pause_reason: Optional[str] = None
    
    # Dynamic pricing parameters (can be updated by agent)
    target_iv: Decimal
    skew_factor: Decimal = Decimal("0")          # IV adjustment per delta
    spread_bps: int = 50                          # Bid-ask spread in basis points
    min_iv: Decimal = Decimal("0.10")            # IV floor
    max_iv: Decimal = Decimal("2.00")            # IV cap
    
    # Risk limits
    max_delta: Decimal = Decimal("1.0")
    max_gamma: Decimal = Decimal("2.0")
    max_vega: Decimal = Decimal("500")
    
    # Agent tracking
    last_agent_update: Optional[datetime] = None
    
    legs: List[AmmLeg] = Field(default_factory=list)

