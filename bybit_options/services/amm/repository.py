from typing import List, Optional
from decimal import Decimal
from bybit_options.services.delta.database_config import db
from .models import AmmStrategy, AmmLeg, AmmOrder

class AmmRepository:
    """
    Direct DB access for AMM Service.
    Uses database_config.db singleton (asyncpg).
    """
    
    async def get_active_strategies(self) -> List[AmmStrategy]:
        """Fetch all strategies marked as active."""
        query = """
            SELECT * FROM amm_strategies WHERE is_active = TRUE
        """
        rows = await db.fetch(query)
        strategies = []
        for row in rows:
            s_dict = dict(row)
            # Fetch Legs
            legs = await self.get_legs_for_strategy(s_dict["id"])
            s_model = AmmStrategy(**s_dict, legs=legs)
            strategies.append(s_model)
        return strategies

    async def get_legs_for_strategy(self, strategy_id: int) -> List[AmmLeg]:
        query = "SELECT * FROM amm_legs WHERE strategy_id = $1"
        rows = await db.fetch(query, strategy_id)
        return [AmmLeg(**dict(row)) for row in rows]

    async def get_orders_for_leg(self, leg_id: int) -> List[AmmOrder]:
        query = "SELECT * FROM amm_orders WHERE leg_id = $1 AND status IN ('NEW', 'ACTIVE')"
        rows = await db.fetch(query, leg_id)
        return [AmmOrder(**dict(row)) for row in rows]
    
    async def create_strategy(self, strategy: AmmStrategy) -> int:
        """Insert a new strategy and return its ID."""
        query = """
            INSERT INTO amm_strategies (name, target_iv, is_active, max_delta, max_gamma, max_vega)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id
        """
        # Note: Using defaults for others
        sid = await db.fetch(query, strategy.name, strategy.target_iv, strategy.is_active, 
                             strategy.max_delta, strategy.max_gamma, strategy.max_vega)
        return sid[0]['id']

    async def create_leg(self, leg: AmmLeg) -> int:
        query = """
            INSERT INTO amm_legs (strategy_id, symbol, side, ratio, target_size)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
        """
        lid = await db.fetch(query, leg.strategy_id, leg.symbol, leg.side, leg.ratio, leg.target_size)
        return lid[0]['id']

    async def save_order(self, order: AmmOrder) -> int:
        query = """
            INSERT INTO amm_orders (leg_id, bybit_order_link_id, price, iv_at_creation, status)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
        """
        oid = await db.fetch(query, order.leg_id, order.bybit_order_link_id, order.price, order.iv_at_creation, order.status)
        return oid[0]['id']
        
    async def update_order_status(self, link_id: str, status: str, bybit_id: Optional[str] = None):
        if bybit_id:
            query = "UPDATE amm_orders SET status = $1, bybit_order_id = $2, last_updated = NOW() WHERE bybit_order_link_id = $3"
            await db.execute(query, status, bybit_id, link_id)
        else:
            query = "UPDATE amm_orders SET status = $1, last_updated = NOW() WHERE bybit_order_link_id = $2"
            await db.execute(query, status, link_id)
    
    async def insert_risk_decision(
        self,
        decision_type: str,
        decision: str,
        strategy_id: Optional[int],
        leg_id: Optional[int],
        portfolio_delta: float,
        portfolio_gamma: float,
        portfolio_vega: float,
        delta_limit: float,
        gamma_limit: float,
        vega_limit: float,
        reason: Optional[str]
    ):
        """Insert risk decision into audit log for Gatekeeper."""
        query = """
            INSERT INTO risk_decisions (
                decision_type, decision, strategy_id, leg_id,
                portfolio_delta, portfolio_gamma, portfolio_vega,
                delta_limit, gamma_limit, vega_limit, reason
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        """
        await db.execute(
            query,
            decision_type, decision, strategy_id, leg_id,
            portfolio_delta, portfolio_gamma, portfolio_vega,
            delta_limit, gamma_limit, vega_limit, reason
        )
