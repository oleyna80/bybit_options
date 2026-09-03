"""
FastAPI Integration Example
Demonstrates how to expose the risk engine as REST endpoints

To run:
    pip install fastapi uvicorn
    uvicorn bybit_options.api.app:app --reload --host 0.0.0.0 --port 8000
"""
import asyncio
import os
import logging
from typing import Dict, Optional, List
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

from fastapi import (
    FastAPI,
    HTTPException,
    Depends,
    Query,
    WebSocket,
    Header,
    status
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession

from bybit_options.services.bybit_connector import BybitConnector
from bybit_options.orchestration.analysis_orchestrator import AnalysisOrchestrator
from bybit_options.models import (
    PortfolioRiskModel,
    CoinRiskModel,
    MarginModel,
    PriceHistoryResponse,
    IVHistoryResponse,
    IVRankHistoryResponse,
    OptionsBoardResponse,
)
from payoff_calculator import calculate_payoff_for_api
from option_board_utils import (
    parse_option_symbol,
    format_option_display,
    calculate_board_statistics,
    sort_options_for_display,
    get_all_option_series,
    fetch_option_tickers
)
from websocket_manager import WebSocketManager

# Strategy modules
from strategy.data.deribit_client import DeribitClient
from strategy.data.data_collector import DataCollector
from strategy.data.candle_manager import CandleManager
from strategy.indicators.bollinger import BollingerBands
from strategy.indicators.regime_detector import analyze_regime

# NEW: Service for DB Access
from iv_rank_service import get_iv_rank_service, IVRankService
# Note: Ensure init_db_on_startup is available in database.py or similar
from database import init_db as init_db_on_startup, AsyncSessionLocal, get_db
from trade_logger import PositionEntry
from bybit_options.api.routes import trade_history_router, delta_router

# Delta Services - optional, can be enabled via ENABLE_DELTA_SERVICES=true
ENABLE_DELTA_SERVICES = os.getenv("ENABLE_DELTA_SERVICES", "false").lower() == "true"
if ENABLE_DELTA_SERVICES:
    from bybit_options.services.delta import TradeIngestor, OrderbookIngestor, DeltaCalculator
else:
    TradeIngestor = None
    OrderbookIngestor = None
    DeltaCalculator = None

load_dotenv()
logger = logging.getLogger(__name__)

# ============================================================================
# SECURITY & CORS CONFIG
# ============================================================================

def _parse_origins(raw: str) -> List[str]:
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


ALLOWED_ORIGINS = _parse_origins(
    os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:3001")
)
# Optional bearer token auth for production; if not set, auth is disabled (dev)
API_AUTH_TOKEN = os.getenv("API_AUTH_TOKEN")


def require_auth(authorization: str = Header(None)):
    """
    Require Bearer token if API_AUTH_TOKEN is set.
    Skip enforcement for local/dev when the env var is absent.
    """
    if not API_AUTH_TOKEN:
        return None
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Missing Bearer token"
        )
    
    token = authorization.split(" ", 1)[1].strip()
    if token != API_AUTH_TOKEN:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Invalid token"
        )
    
    return None

# ============================================================================
# GLOBAL STATE & LIFESPAN
# ============================================================================

_connector: Optional[BybitConnector] = None
_ws_manager: Optional[WebSocketManager] = None
_ws_broadcast_task: Optional[asyncio.Task] = None
_trade_ingestor: Optional[TradeIngestor] = None
_ob_ingestor: Optional[OrderbookIngestor] = None
_delta_calculator: Optional[DeltaCalculator] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global _connector, _ws_manager, _trade_ingestor, _ob_ingestor, _delta_calculator, _ws_broadcast_task
    
    # 1. Init Bybit Connector
    api_key = os.getenv("BYBIT_API_KEY")
    api_secret = os.getenv("BYBIT_API_SECRET")
    
    if not api_key or not api_secret:
        raise RuntimeError("Missing BYBIT_API_KEY or BYBIT_API_SECRET")
    
    _connector = BybitConnector(api_key=api_key, api_secret=api_secret, testnet=False)
    await _connector.connect()
    logger.info("✅ Bybit connector initialized")
    
    # 2. Init Database (Ensure tables exist)
    try:
        await init_db_on_startup()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database init failed: {e}")
        
    # 2.1 Init Delta Database Pool
    try:
        from bybit_options.services.delta.database_config import db as delta_db
        await delta_db.connect()
        logger.info("✅ Delta database pool initialized")
    except Exception as e:
        logger.error(f"❌ Delta database init failed: {e}")
        
    # 2.2 Init Delta Services (optional - set ENABLE_DELTA_SERVICES=true to enable)
    if ENABLE_DELTA_SERVICES:
        try:
            symbols_to_monitor = ["BTCUSDT", "ETHUSDT"]
            _trade_ingestor = TradeIngestor(AsyncSessionLocal, symbols_to_monitor)
            _ob_ingestor = OrderbookIngestor(AsyncSessionLocal, symbols_to_monitor)
            _delta_calculator = DeltaCalculator(AsyncSessionLocal)
            
            await _trade_ingestor.start()
            await _ob_ingestor.start()
            await _delta_calculator.start()
            logger.info("✅ Delta Services started")
        except Exception as e:
            logger.error(f"❌ Delta Services init failed: {e}")
    else:
        logger.info("⏭️ Delta Services disabled (set ENABLE_DELTA_SERVICES=true to enable)")
    
    # 3. Init WebSocket Manager
    _ws_manager = WebSocketManager(broadcast_interval=5.0)
    logger.info("✅ WebSocket manager initialized")

    async def _portfolio_provider() -> Optional[PortfolioRiskModel]:
        # Avoid heavy API calls when no clients are connected.
        if not _ws_manager or not _ws_manager.active_connections:
            return None
        try:
            orchestrator = AnalysisOrchestrator(_connector)
            return await orchestrator.run_full_analysis(fetch_enhanced_metrics=False)
        except Exception as exc:
            logger.error(f"Portfolio provider failed: {exc}")
            return None

    _ws_broadcast_task = asyncio.create_task(
        _ws_manager.start_broadcast_loop(_portfolio_provider)
    )
    
    yield
    
    # Cleanup
    if _connector:
        await _connector.close()
    if _ws_manager:
        _ws_manager.stop_broadcast_loop()
    if _ws_broadcast_task:
        _ws_broadcast_task.cancel()
        try:
            await _ws_broadcast_task
        except asyncio.CancelledError:
            pass
            
    if ENABLE_DELTA_SERVICES:
        if _trade_ingestor: await _trade_ingestor.stop()
        if _ob_ingestor: await _ob_ingestor.stop()
        if _delta_calculator: await _delta_calculator.stop()
        
    # Close Delta database pool
    try:
        from bybit_options.services.delta.database_config import db as delta_db
        await delta_db.close()
        logger.info("✅ Delta database pool closed")
    except Exception as e:
        logger.error(f"❌ Delta database close failed: {e}")
        
    logger.info("🛑 Services stopped")


app = FastAPI(
    title="Bybit Options Risk Engine",
    version="1.1.0",
    lifespan=lifespan,
    dependencies=[Depends(require_auth)]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS or ["http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trade_history_router)
app.include_router(delta_router)

# ============================================================================
# DEPENDENCIES
# ============================================================================

async def get_orchestrator() -> AnalysisOrchestrator:
    if not _connector:
        raise HTTPException(503, "Service not initialized")
    return AnalysisOrchestrator(_connector)

async def get_ws_manager() -> WebSocketManager:
    if not _ws_manager:
        raise HTTPException(503, "WebSocket manager not initialized")
    return _ws_manager

# Dependency for IV Rank Service (DB Access)
async def get_db_service() -> IVRankService:
    return get_iv_rank_service()


async def _get_latest_dvol_snapshot() -> Optional[Dict[str, float]]:
    query = text(
        """
        SELECT timestamp, dvol, ivr
        FROM dvol_history
        ORDER BY timestamp DESC
        LIMIT 1
        """
    )
    async with AsyncSessionLocal() as session:
        result = await session.execute(query)
        row = result.fetchone()

    if not row:
        return None

    return {
        "timestamp": row[0].isoformat() if row[0] else None,
        "dvol": float(row[1]) if row[1] is not None else None,
        "ivr": float(row[2]) if row[2] is not None else None,
    }


async def _calculate_ivr_for_value(current_dvol: float) -> Optional[float]:
    window_start = datetime.now(timezone.utc) - timedelta(days=30)
    query = text(
        """
        SELECT MIN(dvol) AS min_dvol, MAX(dvol) AS max_dvol
        FROM dvol_history
        WHERE timestamp >= :start_time
        """
    )
    async with AsyncSessionLocal() as session:
        result = await session.execute(query, {"start_time": window_start})
        row = result.fetchone()

    if not row or row[0] is None or row[1] is None:
        return None

    min_dvol, max_dvol = float(row[0]), float(row[1])
    if max_dvol - min_dvol <= 0:
        return None

    return ((current_dvol - min_dvol) / (max_dvol - min_dvol)) * 100

# ============================================================================
# RISK & PORTFOLIO ENDPOINTS
# ============================================================================

@app.get("/api/v1/risk/portfolio", response_model=PortfolioRiskModel)
async def get_portfolio_risk(
    enhanced_metrics: bool = Query(True),
    orchestrator: AnalysisOrchestrator = Depends(get_orchestrator)
):
    try:
        return await orchestrator.run_full_analysis(fetch_enhanced_metrics=enhanced_metrics)
    except Exception as e:
        logger.error(f"Portfolio analysis failed: {e}")
        raise HTTPException(500, str(e))

@app.get("/api/v1/risk/coin/{coin}", response_model=CoinRiskModel)
async def get_coin_risk(
    coin: str,
    orchestrator: AnalysisOrchestrator = Depends(get_orchestrator)
):
    try:
        portfolio = await orchestrator.run_full_analysis(fetch_enhanced_metrics=False)
        coin_upper = coin.upper()
        if coin_upper not in portfolio.coin_risks:
            raise HTTPException(404, f"No positions for {coin_upper}")
        return portfolio.coin_risks[coin_upper]
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/api/v1/margin", response_model=MarginModel)
async def get_margin(orchestrator: AnalysisOrchestrator = Depends(get_orchestrator)):
    return await orchestrator.market_data.fetch_margin_info()

@app.get("/api/v1/positions")
async def get_positions(
    base_coin: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    orchestrator: AnalysisOrchestrator = Depends(get_orchestrator)
):
    """
    Get current positions with Entry IV
    
    Returns:
    {
        "count": 9,
        "positions": [
            {
                ...existing fields...,
                "entry_iv": 52.30,
                "current_iv": "0.542",
                "markIv": "0.542"
            }
        ]
    }
    
    Note:
    - entry_iv: stored as fraction in DB (0.523), returned as percentage (52.3)
    - current_iv: added as alias, always matches markIv
    - markIv: unchanged for backward compatibility
    """
    try:
        raw_positions = await orchestrator.market_data.fetch_all_positions()
        
        if base_coin:
            base_upper = base_coin.upper()
            raw_positions = [
                p for p in raw_positions
                if p.get("symbol", "").startswith(base_upper)
            ]
        
        base_coins = set()
        for pos in raw_positions:
            symbol = pos.get("symbol", "")
            if symbol:
                base_coin_extracted = symbol.split("-")[0] if "-" in symbol else symbol[:3]
                base_coins.add(base_coin_extracted)
        
        iv_map = {}
        for coin in base_coins:
            try:
                if not _connector:
                    raise RuntimeError("Connector not initialized")
                tickers = await _connector.get_tickers(category="option", base_coin=coin)
                for ticker in tickers:
                    ticker_symbol = ticker.get("symbol")
                    mark_iv = ticker.get("markIv")
                    if ticker_symbol and mark_iv:
                        iv_map[ticker_symbol] = mark_iv
            except Exception as e:
                logger.error(f"Failed to fetch tickers for {coin}: {e}")
        
        for position in raw_positions:
            symbol = position.get("symbol")
            if not symbol:
                position["entry_iv"] = None
                continue
            
            query = select(PositionEntry).where(PositionEntry.symbol == symbol)
            result = await db.execute(query)
            entry = result.scalar_one_or_none()
            
            if entry and entry.entry_iv:
                position["entry_iv"] = float(entry.entry_iv) * 100
            else:
                position["entry_iv"] = None
            
            if symbol in iv_map:
                position["markIv"] = iv_map[symbol]
                position["current_iv"] = iv_map[symbol]
            else:
                position["markIv"] = None
                position["current_iv"] = None
        
        return {"count": len(raw_positions), "positions": raw_positions}
    
    except Exception as e:
        logger.error(f"Failed to fetch positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# MARKET DATA & OPTIONS BOARD
# ============================================================================

@app.get("/api/v1/options-board", response_model=OptionsBoardResponse)
async def get_options_board(
    base_coin: str = Query("BTC"),
    expiry: Optional[str] = None,
    option_type: Optional[str] = None,
    sort_by: str = "strike",
    sort_order: str = "asc",
    limit: int = Query(50, ge=1, le=500),
    orchestrator: AnalysisOrchestrator = Depends(get_orchestrator)
):
    # Logic unchanged - keeping your existing robust implementation
    # ... (omitted for brevity, assume full logic from your file is here)
    # Use the implementation from your provided file for this specific function
    try:
        # 1. Underlying Price
        underlying_price = 0
        try:
            tickers = await _connector.get_tickers(category="spot", symbol=f"{base_coin}USDT")
            if tickers: underlying_price = float(tickers[0].get("lastPrice", 0))
        except: pass

        # 2. Fetch Series
        all_series = await get_all_option_series(_connector, base_coin)
        selected_series = [expiry] if expiry else (all_series[:3] if len(all_series) > 3 else all_series)

        # 3. Fetch Instruments
        all_instruments = []
        for series in selected_series:
            instr = await _connector.get_instruments_info(category="option", base_coin=base_coin)
            all_instruments.extend([i for i in instr if series in i.get("symbol", "")])

        # 4. Extract Symbols & Fetch Data
        symbols = [i.get("symbol") for i in all_instruments if i.get("symbol")]
        if option_type:
            option_type_normalized = option_type.upper()
            if option_type_normalized in {"CALL", "C"}:
                code = "C"
            elif option_type_normalized in {"PUT", "P"}:
                code = "P"
            else:
                raise HTTPException(400, "option_type must be CALL/PUT/C/P")
            symbols = [s for s in symbols if s.endswith(f"-{code}")]
        
        # Limit for MVP performance
        symbols = symbols[:limit]
        ticker_data = await fetch_option_tickers(_connector, symbols)

        # 5. Format
        formatted = []
        for sym in symbols:
            if sym not in ticker_data: continue
            formatted.append(format_option_display(
                parse_option_symbol(sym), ticker_data[sym], underlying_price
            ))

        sort_order_normalized = sort_order.lower()
        if sort_order_normalized not in {"asc", "desc"}:
            raise HTTPException(400, "sort_order must be asc or desc")

        sorted_options = sort_options_for_display(formatted, sort_by, sort_order_normalized)
        return OptionsBoardResponse(
            base_coin=base_coin.upper(),
            underlying_price=underlying_price,
            options=sorted_options,
            options_count=len(sorted_options),
            series=selected_series,
            expiry=expiry,
            option_type=option_type,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
        )
    except Exception as e:
        logger.error(f"Options board error: {e}")
        raise HTTPException(500, str(e))


@app.get("/api/v1/payoff-chart")
async def get_payoff_chart(
    base_coin: str = Query("BTC"),
    days_to_expiry: Optional[int] = Query(None, ge=0),
    price_range_pct: float = Query(20.0, ge=1.0, le=100.0),
    include_theta: bool = Query(False),
    orchestrator: AnalysisOrchestrator = Depends(get_orchestrator),
):
    base_coin = base_coin.upper()
    try:
        portfolio = await orchestrator.run_full_analysis(fetch_enhanced_metrics=False)

        positions = []
        current_prices: Dict[str, float] = {}
        for coin, coin_risk in portfolio.coin_risks.items():
            current_prices[coin] = coin_risk.underlying_price or 0.0
            positions.extend(coin_risk.positions)

        payoff_data = calculate_payoff_for_api(
            positions=positions,
            current_prices=current_prices,
            base_coin=base_coin,
            price_range_pct=price_range_pct,
            days_to_expiry=days_to_expiry,
            include_theta=include_theta,
        )

        coin_risk = portfolio.coin_risks.get(base_coin)
        if coin_risk:
            payoff_data["portfolio_summary"] = {
                "base_coin": base_coin,
                "delta_coin": coin_risk.total_greeks.delta_coin,
                "gamma_coin": coin_risk.total_greeks.gamma_coin,
                "vega_usd": coin_risk.total_greeks.vega_usd,
                "theta_usd": coin_risk.total_greeks.theta_usd,
            }
        else:
            payoff_data["portfolio_summary"] = {
                "base_coin": base_coin,
                "delta_coin": 0.0,
                "gamma_coin": 0.0,
                "vega_usd": 0.0,
                "theta_usd": 0.0,
            }

        return payoff_data
    except Exception as e:
        logger.error(f"Payoff chart error: {e}")
        raise HTTPException(500, str(e))

# ============================================================================
# HISTORICAL DATA (Powered by PostgreSQL)
# ============================================================================

@app.get(
    "/api/v1/price-history",
    response_model=PriceHistoryResponse,
    summary="Get historical OHLCV (Daily)",
    tags=["History"]
)
async def get_price_history(
    symbol: str = Query("BTCUSDT", description="Perpetual symbol"),
    days: int = Query(365, ge=7, le=730),
    db_service: IVRankService = Depends(get_db_service)
):
    """
    Fetch historical Price Data from Database (PostgreSQL).
    This data ensures the chart matches the volatility calculations.
    """
    try:
        ohlcv_data = await db_service.get_perpetual_ohlcv(symbol=symbol, limit=days)
        
        if not ohlcv_data:
            # Fallback warning if DB is empty
            logger.warning(f"No DB data for {symbol}. Run backfill!")
            return PriceHistoryResponse(symbol=symbol, candles=[])
            
        return PriceHistoryResponse(symbol=symbol, candles=ohlcv_data)
        
    except Exception as e:
        logger.error(f"DB Error: {e}")
        raise HTTPException(500, f"Database error: {str(e)}")


@app.get(
    "/api/v1/iv-rank",
    response_model=IVRankHistoryResponse,
    summary="Get IV Rank History",
    tags=["History"]
)
async def get_iv_rank_history(
    base_coin: str = Query("BTC"),
    days: int = Query(365, ge=30, le=730),
    db_service: IVRankService = Depends(get_db_service)
):
    """
    Fetch IV Rank History from Database.
    Includes: Rank (0-100), Current IV, and Min/Max bounds.
    """
    try:
        data = await db_service.get_iv_rank_history(base_coin=base_coin, days=days)
        
        if not data:
            raise HTTPException(404, f"No IV Rank data for {base_coin}. Run backfill.")
            
        return IVRankHistoryResponse(base_coin=base_coin, iv_rank_data=data)
        
    except HTTPException: raise
    except Exception as e:
        logger.error(f"DB Error: {e}")
        raise HTTPException(500, str(e))

# ============================================================================
# STRATEGY ENDPOINTS (Sigma-Fractal Phase 1)
# ============================================================================

@app.get("/api/v1/strategy/dvol")
async def get_strategy_dvol():
    try:
        async with DeribitClient() as client:
            snapshot = await client.get_volatility_index("BTC")
        ivr = await _calculate_ivr_for_value(float(snapshot["dvol"]))
        return {
            "dvol": snapshot["dvol"],
            "timestamp": snapshot["timestamp"],
            "ivr": ivr,
        }
    except Exception as e:
        logger.error(f"Deribit DVOL fetch failed: {e}")
        raise HTTPException(500, str(e))


@app.get("/api/v1/strategy/regime")
async def get_strategy_regime(base_coin: str = Query("BTC")):
    if not _connector:
        raise HTTPException(503, "Service not initialized")

    symbol = f"{base_coin.upper()}USDT"
    candle_manager = CandleManager(_connector)

    d1_candles = await candle_manager.get_d1_candles(symbol=symbol, days=200)
    closes = [c["close"] for c in d1_candles]
    bb_width_history = BollingerBands().bb_width_history(closes)

    regime = analyze_regime(d1_candles, bb_width_history)
    latest_dvol = await _get_latest_dvol_snapshot()

    return {
        **regime,
        "dvol": latest_dvol["dvol"] if latest_dvol else None,
        "ivr": latest_dvol["ivr"] if latest_dvol else None,
    }


@app.post("/api/v1/strategy/collect-snapshot")
async def collect_strategy_snapshot():
    try:
        collector = DataCollector()
        async with collector.client:
            result = await collector.collect_dvol_snapshot()
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"DVOL collection failed: {e}")
        raise HTTPException(500, str(e))

# ============================================================================
# WEBSOCKETS
# ============================================================================

@app.websocket("/ws/portfolio")
async def websocket_portfolio(websocket: WebSocket, ws_manager: WebSocketManager = Depends(get_ws_manager)):
    client_id = await ws_manager.connect(websocket)
    try:
        await ws_manager.handle_client(client_id)
    except Exception as e:
        await ws_manager.disconnect(client_id)

# ============================================================================
# AMM ROBOT API (Stage 5: GUI Dashboard)
# ============================================================================

@app.get("/api/v1/amm/strategies")
async def get_amm_strategies():
    """Get all AMM strategies with their legs and active orders."""
    try:
        from bybit_options.services.amm.repository import AmmRepository
        repo = AmmRepository()
        strategies = await repo.get_active_strategies()
        
        # Convert to dict for JSON serialization
        result = []
        for s in strategies:
            # Determine symbol from first leg (if available)
            symbol = "BTC"  # Default
            if s.legs:
                first_leg_symbol = s.legs[0].symbol
                # Extract base coin from symbol (e.g., "BTC-26JAN24-100000-C" -> "BTC")
                if "-" in first_leg_symbol:
                    symbol = first_leg_symbol.split("-")[0]
            
            # Determine status
            status = "PAUSED" if s.is_paused else ("ACTIVE" if s.is_active else "INACTIVE")
            
            strategy_dict = {
                "id": s.id,
                "name": s.name,
                "symbol": symbol,  # Added for frontend
                "status": status,  # Added for frontend
                "target_iv": float(s.target_iv),
                "is_active": s.is_active,
                "is_paused": s.is_paused,
                "max_delta": float(s.max_delta) if s.max_delta else None,
                "max_gamma": float(s.max_gamma) if s.max_gamma else None,
                "max_vega": float(s.max_vega) if s.max_vega else None,
                "skew_factor": float(s.skew_factor) if s.skew_factor is not None else 1.0,
                "spread_bps": int(s.spread_bps) if s.spread_bps is not None else 50,
                "min_iv": float(s.min_iv) if s.min_iv else 0.10,
                "max_iv": float(s.max_iv) if s.max_iv else 2.00,
                "created_at": s.created_at.isoformat() if hasattr(s, 'created_at') and s.created_at else datetime.now(timezone.utc).isoformat(),
                "updated_at": s.last_agent_update.isoformat() if s.last_agent_update else datetime.now(timezone.utc).isoformat(),
                "last_agent_update": s.last_agent_update.isoformat() if s.last_agent_update else None,
                "legs": [
                    {
                        "id": leg.id,
                        "symbol": leg.symbol,
                        "side": leg.side,
                        "ratio": float(leg.ratio),
                        "target_size": float(leg.target_size),
                        "total_filled": float(leg.total_filled) if leg.total_filled else 0,
                        "is_active": leg.is_active,
                        "active_order": {
                            "price": float(leg.active_order.price),
                            "status": leg.active_order.status,
                            "bybit_order_id": leg.active_order.bybit_order_id
                        } if leg.active_order else None
                    }
                    for leg in s.legs
                ]
            }
            result.append(strategy_dict)
        
        return {"strategies": result}
    except Exception as e:
        logging.error(f"Failed to fetch AMM strategies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/amm/strategies")
async def create_amm_strategy(request: dict):
    """Create a new AMM strategy with legs."""
    try:
        from bybit_options.services.amm.repository import AmmRepository
        from bybit_options.services.amm.models import AmmStrategy, AmmLeg
        
        repo = AmmRepository()
        
        # Create strategy
        strategy = AmmStrategy(
            name=request.get("name"),
            target_iv=request.get("target_iv", 0.65),  # Default to 65% IV
            is_active=True,
            is_paused=False,
            max_delta=request.get("max_delta", 1.0),
            max_gamma=request.get("max_gamma", 0.05),
            max_vega=request.get("max_vega", 5000.0),
            skew_factor=request.get("skew_factor", 1.0),  # Default to neutral skew
            spread_bps=request.get("spread_bps", 50),
            min_iv=request.get("min_iv", 0.10),
            max_iv=request.get("max_iv", 2.00),
            legs=[]
        )
        
        strategy_id = await repo.create_strategy(strategy)
        
        # Create legs if provided
        legs_data = request.get("legs", [])
        leg_ids = []
        for leg_data in legs_data:
            leg = AmmLeg(
                strategy_id=strategy_id,
                symbol=leg_data.get("symbol"),
                side=leg_data.get("side"),
                ratio=leg_data.get("ratio", 1.0),
                target_size=leg_data.get("target_size"),
                is_active=True
            )
            leg_id = await repo.create_leg(leg)
            leg_ids.append(leg_id)
        
        return {
            "id": strategy_id,
            "status": "created",
            "legs_created": len(leg_ids)
        }
    except Exception as e:
        logging.error(f"Failed to create AMM strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/v1/amm/strategies/{strategy_id}")
async def update_amm_strategy(
    strategy_id: int,
    is_paused: Optional[bool] = None,
    target_iv: Optional[float] = None
):
    """Update AMM strategy (pause/resume or change target IV)."""
    try:
        query_parts = []
        params = []
        
        if is_paused is not None:
            query_parts.append("is_paused = $1")
            params.append(is_paused)
        
        if target_iv is not None:
            query_parts.append(f"target_iv = ${len(params) + 1}")
            params.append(target_iv)
        
        if not query_parts:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        params.append(strategy_id)
        query = f"UPDATE amm_strategies SET {', '.join(query_parts)} WHERE id = ${len(params)}"
        
        from bybit_options.services.delta.database_config import db
        await db.execute(query, *params)
        
        return {"status": "updated"}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Failed to update AMM strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/amm/strategies/{strategy_id}")
async def delete_amm_strategy(strategy_id: int):
    """Delete AMM strategy and all its legs."""
    try:
        from bybit_options.services.delta.database_config import db
        
        # Delete legs first (foreign key constraint)
        await db.execute("DELETE FROM amm_legs WHERE strategy_id = $1", strategy_id)
        await db.execute("DELETE FROM amm_strategies WHERE id = $1", strategy_id)
        
        return {"status": "deleted"}
    except Exception as e:
        logging.error(f"Failed to delete AMM strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/amm/portfolio/greeks")
async def get_portfolio_greeks():
    """Get current portfolio Greeks (aggregated across all strategies)."""
    try:
        from bybit_options.services.amm.repository import AmmRepository
        from bybit_options.services.amm.greeks_aggregator import GreeksAggregator
        from bybit_options.services.amm.time_calculator import calculate_time_to_expiry
        from bybit_options.core.risk_engine import RiskEngine
        from bybit_options.services.delta.database_config import db
        
        repo = AmmRepository()
        aggregator = GreeksAggregator()
        
        # Get active strategies
        strategies = await repo.get_active_strategies()
        
        # Get real spot prices from database (latest tickers)
        await db.connect()
        spot_prices = {}
        
        # Get real spot prices from database (latest tickers)
        await db.connect()
        spot_prices = {}
        
        # Fetch BTC and ETH spot prices from perpetual_ohlcv table (using fast 1m candles)
        async with db.acquire() as conn:
            btc_ticker = await conn.fetchrow(
                "SELECT close FROM perpetual_ohlcv WHERE symbol = 'BTCUSDT' ORDER BY timestamp DESC LIMIT 1"
            )
            eth_ticker = await conn.fetchrow(
                "SELECT close FROM perpetual_ohlcv WHERE symbol = 'ETHUSDT' ORDER BY timestamp DESC LIMIT 1"
            )
            
            if btc_ticker:
                spot_prices["BTC"] = float(btc_ticker["close"])
            else:
                spot_prices["BTC"] = 100000.0  # Fallback if no data
                
            if eth_ticker:
                spot_prices["ETH"] = float(eth_ticker["close"])
            else:
                spot_prices["ETH"] = 3500.0  # Fallback if no data
        
        # Get market IVs and time to expiries from strategy defaults (since option_tickers table is missing)
        market_ivs = {}
        time_to_expiries = {}
        
        # Also fetch real positions from position_entries to include in portfolio Greeks
        # This ensures we show TOTAL portfolio risk, not just AMM strategies
        raw_positions = []
        async with db.acquire() as conn:
            # Check if table exists
            exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'position_entries'
                );
            """)
            
            if exists:
                raw_positions = await conn.fetch("SELECT symbol, net_qty FROM position_entries WHERE net_qty != 0")

        # Create a virtual strategy for existing non-AMM positions
        from bybit_options.services.amm.models import AmmStrategy, AmmLeg
        
        external_legs = []
        for pos in raw_positions:
            symbol = pos['symbol']
            size = float(pos['net_qty'])
            
            # Skip if this position is already covered by an AMM leg (simple deduplication by symbol check could be improved)
            # For now, since amm_legs is empty as per diagnosis, we just add everything
            
            leg = AmmLeg(
                id=0, # Virtual ID
                strategy_id=0,
                symbol=symbol,
                side="BUY" if size > 0 else "SELL",
                ratio=1.0,
                target_size=abs(size),
                total_filled=abs(size),
                is_active=True
            )
            external_legs.append(leg)
            
            # Register for market data
            market_ivs[symbol] = 0.65 # Default fallback
            try:
                time_to_expiries[symbol] = calculate_time_to_expiry(symbol)
            except:
                time_to_expiries[symbol] = 0.5

        if external_legs:
            # Create a virtual strategy container
            virtual_strategy = AmmStrategy(
                name="External Positions",
                is_active=True,
                legs=external_legs,
                target_iv=0.65 # Default IV for external positions
            )
            strategies.append(virtual_strategy)

        # Ensure market data for existing AMM strategies is also prepared
        for s in strategies:
            if s.name == "External Positions":
                continue # Already handled
                
            for leg in s.legs:
                symbol = leg.symbol
                market_ivs[symbol] = float(s.target_iv) if s.target_iv else 0.65
                try:
                    time_to_expiries[symbol] = calculate_time_to_expiry(symbol)
                except:
                    time_to_expiries[symbol] = 0.5

        # Calculate portfolio Greeks
        portfolio = aggregator.calculate(strategies, spot_prices, market_ivs, time_to_expiries)
        
        return {
            "delta": portfolio.delta,
            "gamma": portfolio.gamma,
            "vega": portfolio.vega,
            "theta": portfolio.theta,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logging.error(f"Failed to calculate portfolio Greeks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/amm/risk/decisions")
async def get_risk_decisions(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """Get risk decisions log (paginated)."""
    try:
        from bybit_options.services.delta.database_config import db
        
        # Get total count
        count_query = "SELECT COUNT(*) FROM risk_decisions"
        total = await db.fetchrow(count_query)
        
        # Get paginated results
        query = """
            SELECT 
                id, decision_time, decision_type, decision,
                portfolio_delta, portfolio_gamma, portfolio_vega,
                reason, strategy_id, leg_id
            FROM risk_decisions
            ORDER BY decision_time DESC
            LIMIT $1 OFFSET $2
        """
        rows = await db.fetch(query, limit, offset)
        
        decisions = [
            {
                "id": row["id"],
                "decision_time": row["decision_time"].isoformat() if row["decision_time"] else None,
                "decision_type": row["decision_type"],
                "decision": row["decision"],
                "portfolio_delta": float(row["portfolio_delta"]) if row["portfolio_delta"] else None,
                "portfolio_gamma": float(row["portfolio_gamma"]) if row["portfolio_gamma"] else None,
                "portfolio_vega": float(row["portfolio_vega"]) if row["portfolio_vega"] else None,
                "reason": row["reason"],
                "strategy_id": row["strategy_id"],
                "leg_id": row["leg_id"]
            }
            for row in rows
        ]
        
        return {
            "decisions": decisions,
            "total": total[0] if total else 0,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logging.error(f"Failed to fetch risk decisions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/amm/status")
async def get_amm_status():
    """Get AMM engine status."""
    # In production, this would check the actual engine state
    # For now, return mock data
    try:
        from bybit_options.services.delta.database_config import db
        
        # Count active/paused strategies
        active_count = await db.fetchrow(
            "SELECT COUNT(*) FROM amm_strategies WHERE is_active = TRUE AND is_paused = FALSE"
        )
        paused_count = await db.fetchrow(
            "SELECT COUNT(*) FROM amm_strategies WHERE is_active = TRUE AND is_paused = TRUE"
        )
        
        # Count active orders
        orders_count = await db.fetchrow(
            "SELECT COUNT(*) FROM amm_orders WHERE status IN ('NEW', 'ACTIVE')"
        )
        
        return {
            "is_running": True,  # Mock - in production check engine state
            "last_cycle": datetime.now(timezone.utc).isoformat(),
            "strategies_active": active_count[0] if active_count else 0,
            "strategies_paused": paused_count[0] if paused_count else 0,
            "orders_active": orders_count[0] if orders_count else 0
        }
    except Exception as e:
        logging.error(f"Failed to get AMM status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# AMM Engine singleton (global state for demo - in production use process manager)
_amm_engine = None
_engine_task = None


@app.post("/api/v1/amm/engine/start")
async def start_amm_engine():
    """Start the AMM engine."""
    global _amm_engine, _engine_task
    
    if _amm_engine and _amm_engine.is_running:
        return {"status": "already_running"}
    
    try:
        from bybit_options.services.amm.engine import AmmEngine
        
        _amm_engine = AmmEngine()
        await _amm_engine.initialize()
        
        # Start engine in background task
        _engine_task = asyncio.create_task(_amm_engine.run_loop())
        
        logging.info("AMM Engine started")
        return {"status": "started"}
    except Exception as e:
        logging.error(f"Failed to start AMM engine: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/amm/engine/stop")
async def stop_amm_engine():
    """Stop the AMM engine."""
    global _amm_engine, _engine_task
    
    if not _amm_engine or not _amm_engine.is_running:
        return {"status": "not_running"}
    
    try:
        _amm_engine.is_running = False
        
        # Cancel the background task
        if _engine_task:
            _engine_task.cancel()
            try:
                await _engine_task
            except asyncio.CancelledError:
                pass
        
        logging.info("AMM Engine stopped")
        return {"status": "stopped"}
    except Exception as e:
        logging.error(f"Failed to stop AMM engine: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/amm/strategies/{strategy_id}/legs")
async def add_leg_to_strategy(strategy_id: int, leg_data: dict):
    """Add a leg to an existing strategy."""
    try:
        from bybit_options.services.amm.repository import AmmRepository
        from bybit_options.services.amm.models import AmmLeg
        
        repo = AmmRepository()
        
        leg = AmmLeg(
            strategy_id=strategy_id,
            symbol=leg_data.get("symbol"),
            side=leg_data.get("side"),
            ratio=leg_data.get("ratio", 1.0),
            target_size=leg_data.get("target_size"),
            is_active=True
        )
        
        leg_id = await repo.create_leg(leg)
        return {"id": leg_id, "status": "created"}
    except Exception as e:
        logging.error(f"Failed to add leg: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/amm/strategies/{strategy_id}/legs/{leg_id}")
async def delete_leg(strategy_id: int, leg_id: int):
    """Delete a leg from a strategy."""
    try:
        from bybit_options.services.delta.database_config import db
        
        # Verify leg belongs to strategy
        result = await db.fetchrow(
            "SELECT id FROM amm_legs WHERE id = $1 AND strategy_id = $2",
            leg_id, strategy_id
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Leg not found")
        
        await db.execute("DELETE FROM amm_legs WHERE id = $1", leg_id)
        return {"status": "deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Failed to delete leg: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# AGENT COMMAND API (Trading Expert → AMM Robot)
# ============================================================================

from enum import Enum

class AgentCommandType(str, Enum):
    UPDATE_STRATEGY_PARAMS = "UPDATE_STRATEGY_PARAMS"
    PAUSE_STRATEGY = "PAUSE_STRATEGY"
    RESUME_STRATEGY = "RESUME_STRATEGY"

class OperatingMode(str, Enum):
    MANUAL = "MANUAL"
    AUTO = "AUTO"


@app.post("/api/v1/amm/agent/command")
async def receive_agent_command(command: dict):
    """
    Receive and execute command from Trading Expert.
    
    Commands:
    - UPDATE_STRATEGY_PARAMS: Update target_iv, skew_factor, spread_bps
    - PAUSE_STRATEGY: Pause a strategy
    - RESUME_STRATEGY: Resume a strategy
    """
    from bybit_options.services.delta.database_config import db
    import json
    
    try:
        action = command.get("action")
        strategy_id = command.get("strategy_id")
        params = command.get("params", {})
        reason = command.get("reason", "")
        source = command.get("source", "MANUAL")
        
        if action == "UPDATE_STRATEGY_PARAMS":
            if not strategy_id or not params:
                raise HTTPException(400, "strategy_id and params required")
            
            # Get current params for logging
            old_params = await db.fetchrow(
                """SELECT target_iv, skew_factor, spread_bps, min_iv, max_iv 
                   FROM amm_strategies WHERE id = $1""",
                strategy_id
            )
            
            if not old_params:
                raise HTTPException(404, f"Strategy {strategy_id} not found")
            
            # Build update query
            updates = []
            values = []
            idx = 1
            
            allowed_params = ['target_iv', 'skew_factor', 'spread_bps', 'min_iv', 'max_iv']
            for key, value in params.items():
                if key in allowed_params:
                    updates.append(f"{key} = ${idx}")
                    values.append(value)
                    idx += 1
            
            if not updates:
                raise HTTPException(400, "No valid params to update")
            
            # Add last_agent_update
            updates.append(f"last_agent_update = ${idx}")
            values.append(datetime.now(timezone.utc))
            idx += 1
            
            # Add strategy_id
            values.append(strategy_id)
            
            query = f"UPDATE amm_strategies SET {', '.join(updates)} WHERE id = ${idx}"
            await db.execute(query, *values)
            
            # Log command to audit table
            try:
                await db.execute("""
                    INSERT INTO agent_commands_log 
                    (command_type, strategy_id, old_params, new_params, source, reason)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, action, strategy_id, json.dumps(dict(old_params), default=str), json.dumps(params, default=str), source, reason)
            except Exception as log_error:
                logging.warning(f"Failed to log agent command: {log_error}")

            logging.info(f"[Agent] Updated strategy {strategy_id}: {params}")
            
            return {
                "status": "executed",
                "strategy_id": strategy_id,
                "updated_params": params
            }
        
        elif action == "PAUSE_STRATEGY":
            if not strategy_id:
                raise HTTPException(400, "strategy_id required")
            
            await db.execute(
                "UPDATE amm_strategies SET is_paused = TRUE, pause_reason = $1 WHERE id = $2",
                reason, strategy_id
            )
            
            # Log command
            try:
                await db.execute("""
                    INSERT INTO agent_commands_log 
                    (command_type, strategy_id, source, reason)
                    VALUES ($1, $2, $3, $4)
                """, action, strategy_id, source, reason)
            except Exception as log_error:
                logging.warning(f"Failed to log PAUSE command: {log_error}")

            logging.info(f"[Agent] Paused strategy {strategy_id}: {reason}")
            return {"status": "paused", "strategy_id": strategy_id}
        
        elif action == "RESUME_STRATEGY":
            if not strategy_id:
                raise HTTPException(400, "strategy_id required")
            
            await db.execute(
                "UPDATE amm_strategies SET is_paused = FALSE, pause_reason = NULL WHERE id = $1",
                strategy_id
            )
            
            # Log command
            try:
                await db.execute("""
                    INSERT INTO agent_commands_log 
                    (command_type, strategy_id, source, reason)
                    VALUES ($1, $2, $3, $4)
                """, action, strategy_id, source, reason)
            except Exception as log_error:
                logging.warning(f"Failed to log RESUME command: {log_error}")

            logging.info(f"[Agent] Resumed strategy {strategy_id}")
            return {"status": "resumed", "strategy_id": strategy_id}
        
        else:
            raise HTTPException(400, f"Unknown action: {action}")
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"[Agent] Command failed: {e}")
        raise HTTPException(500, str(e))


@app.post("/api/v1/amm/mode")
async def set_operating_mode(config: dict):
    """
    Switch between MANUAL and AUTO operating modes.
    """
    from bybit_options.services.delta.database_config import db
    
    mode = config.get("mode", "MANUAL")
    interval = config.get("check_interval_minutes", 15)
    
    try:
        await db.execute("""
            UPDATE amm_operating_mode 
            SET mode = $1, check_interval_minutes = $2, updated_at = NOW()
            WHERE id = 1
        """, mode, interval)
        
        logging.info(f"[Agent] Mode set to {mode}, interval={interval}m")
        return {"mode": mode, "check_interval_minutes": interval}
    except Exception as e:
        logging.error(f"Failed to set mode: {e}")
        raise HTTPException(500, str(e))


@app.get("/api/v1/amm/mode")
async def get_operating_mode():
    """Get current operating mode."""
    from bybit_options.services.delta.database_config import db
    
    try:
        row = await db.fetchrow("SELECT mode, check_interval_minutes FROM amm_operating_mode LIMIT 1")
        if row:
            return {"mode": row["mode"], "check_interval_minutes": row["check_interval_minutes"]}
        return {"mode": "MANUAL", "check_interval_minutes": 15}
    except Exception as e:
        logging.error(f"Failed to get mode: {e}")
        return {"mode": "MANUAL", "check_interval_minutes": 15}


@app.get("/api/v1/amm/agent/commands")
async def get_agent_commands_log(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """Get agent commands audit log."""
    from bybit_options.services.delta.database_config import db
    
    try:
        rows = await db.fetch("""
            SELECT id, timestamp, command_type, strategy_id, new_params, source, reason, status
            FROM agent_commands_log
            ORDER BY timestamp DESC
            LIMIT $1 OFFSET $2
        """, limit, offset)
        
        return {
            "commands": [
                {
                    "id": row["id"],
                    "timestamp": row["timestamp"].isoformat() if row["timestamp"] else None,
                    "command_type": row["command_type"],
                    "strategy_id": row["strategy_id"],
                    "params": row["new_params"],
                    "source": row["source"],
                    "reason": row["reason"]
                }
                for row in rows
            ],
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logging.error(f"Failed to get commands log: {e}")
        raise HTTPException(500, str(e))


# ============================================================================
# VOLATILITY INTELLIGENCE API
# ============================================================================

@app.get("/api/v1/volatility/context")
async def get_volatility_context(
    symbol: str = Query("BTC"),
    include_smile: bool = Query(False),
    expiry: Optional[str] = Query(None),
    spot_price: Optional[float] = Query(None)
):
    """
    Get full volatility context for Trading Expert.
    
    Returns IV Rank, HV, IV/HV ratio, and optional smile metrics.
    """
    try:
        from bybit_options.services.volatility import VolatilityContextAPI
        
        api = VolatilityContextAPI()
        context = await api.get_context(symbol, include_smile, expiry, spot_price)
        
        return {
            "symbol": context.symbol,
            "timestamp": context.timestamp.isoformat(),
            "iv_rank": context.iv_rank,
            "iv_regime": context.iv_regime,
            "current_iv": context.current_iv,
            "hv": {
                "hv_7d": context.hv_7d,
                "hv_30d": context.hv_30d,
                "hv_90d": context.hv_90d
            },
            "iv_hv_ratio": context.iv_hv_ratio,
            "signals": {
                "hv_signal": context.hv_signal,
                "overall": context.overall_signal
            },
            "smile": {
                "atm_iv": context.atm_iv,
                "put_skew": context.put_skew,
                "call_skew": context.call_skew,
                "skew_slope": context.skew_slope
            } if include_smile else None
        }
    except Exception as e:
        logging.error(f"Failed to get volatility context: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/volatility/iv-rank/history")
async def get_iv_rank_history(
    symbol: str = Query("BTC"),
    days: int = Query(365, ge=1, le=730)
):
    """
    Get IV Rank history for charting.
    """
    try:
        from bybit_options.services.volatility import IVRankConnector
        
        connector = IVRankConnector()
        history = await connector.get_history(symbol, days)
        
        return {
            "symbol": symbol,
            "count": len(history),
            "data": [
                {
                    "timestamp": h.timestamp.isoformat(),
                    "iv_rank": h.iv_rank,
                    "current_iv": h.current_iv,
                    "regime": h.regime
                }
                for h in history
            ]
        }
    except Exception as e:
        logging.error(f"Failed to get IV Rank history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/volatility/hv")
async def get_historical_volatility(
    symbol: str = Query("BTC"),
    timeframe: str = Query("1d", regex="^(1d|4h)$")
):
    """
    Get Historical Volatility (7/30/90 day windows).
    """
    try:
        from bybit_options.services.volatility import HVCalculator
        
        calc = HVCalculator(timeframe=timeframe)
        hv_data = await calc.calculate(symbol)
        
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "hv_7d": hv_data.hv_7d,
            "hv_30d": hv_data.hv_30d,
            "hv_90d": hv_data.hv_90d,
            "signal": hv_data.signal,
            "timestamp": hv_data.timestamp.isoformat()
        }
    except Exception as e:
        logging.error(f"Failed to get HV: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# TECHNICAL INTELLIGENCE API (Stage 6: TZ-TECH-001)
# ============================================================================

@app.get("/api/v1/technical/alligator")
async def get_alligator_state(
    symbol: str = "BTC",
    timeframe: str = "H4"  # W1, D1, H4, H1
):
    """
    Get Alligator indicator state for a specific timeframe.
    
    Returns current Alligator values and interpreted state (SLEEPING/EATING).
    """
    try:
        from bybit_options.services.technical import AlligatorStateDetector
        from bybit_options.services.technical.context_api import TechnicalContextAPI
        from bybit_options.services.delta.database_config import db
        
        # Initialize API
        api = TechnicalContextAPI(db._pool)
        
        # Load candles for requested timeframe
        symbol_usdt = f"{symbol}USDT"
        candles = await api._load_candles(symbol_usdt, timeframe, 50)
        
        if not candles:
            raise HTTPException(404, f"No candle data found for {symbol} {timeframe}")
        
        # Detect Alligator state
        detector = AlligatorStateDetector()
        context = detector.detect(candles)
        
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "jaw": context.jaw,
            "teeth": context.teeth,
            "lips": context.lips,
            "state": context.state.value,
            "spread_pct": round(context.spread_pct, 4),
            "trend_direction": context.trend_direction,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Failed to get Alligator state: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/technical/fractals")
async def get_key_fractals(
    symbol: str = "BTC",
    timeframe: str = "H4",
    limit: int = 10
):
    """
    Get key fractals (support/resistance levels) for a symbol and timeframe.
    
    Fractals are ordered by most recent first.
    """
    try:
        from bybit_options.services.delta.database_config import db
        
        symbol_usdt = f"{symbol}USDT"
        
        query = """
            SELECT 
                price, 
                fractal_type, 
                candle_time, 
                timeframe,
                is_key_fractal,
                alligator_teeth,
                bb_upper_1sigma,
                bb_lower_1sigma
            FROM fractals_cache
            WHERE symbol = $1 
              AND timeframe = $2 
              AND is_key_fractal = TRUE
            ORDER BY candle_time DESC
            LIMIT $3
        """
        
        await db.connect()
        rows = await db.fetch(query, symbol_usdt, timeframe, limit)
        
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "fractals": [
                {
                    "price": float(row["price"]),
                    "direction": row["fractal_type"],
                    "time": row["candle_time"].isoformat(),
                    "is_key": row["is_key_fractal"],
                    "alligator_teeth": float(row["alligator_teeth"]) if row["alligator_teeth"] else None,
                    "bb_upper_1sigma": float(row["bb_upper_1sigma"]) if row["bb_upper_1sigma"] else None,
                    "bb_lower_1sigma": float(row["bb_lower_1sigma"]) if row["bb_lower_1sigma"] else None
                }
                for row in rows
            ],
            "count": len(rows)
        }
    except Exception as e:
        logging.error(f"Failed to fetch fractals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/technical/context")
async def get_technical_context(symbol: str = "BTC"):
    """
    Get complete technical context with multi-timeframe analysis.
    
    Combines:
    - Alligator states (W1, D1, H4)
    - Nearest key fractals
    - Global trend determination
    - Trading signal for Trading Expert
    """
    try:
        from bybit_options.services.technical import TechnicalContextAPI
        from bybit_options.services.delta.database_config import db
        
        api = TechnicalContextAPI(db._pool)
        context = await api.get_context(symbol)
        
        def serialize_alligator(alg):
            if not alg:
                return None
            return {
                "jaw": alg.jaw,
                "teeth": alg.teeth,
                "lips": alg.lips,
                "state": alg.state.value,
                "spread_pct": alg.spread_pct,
                "trend_direction": alg.trend_direction
            }
        
        def serialize_fractal(frac):
            if not frac:
                return None
            return {
                "price": frac.price,
                "direction": frac.direction,
                "timeframe": frac.timeframe,
                "time": frac.candle_time.isoformat(),
                "distance_pct": round(frac.distance_pct, 2)
            }
        
        return {
            "symbol": context.symbol,
            "timestamp": context.timestamp.isoformat(),
            "current_price": context.current_price,
            "global_trend": context.global_trend,
            "trend_signal": context.trend_signal,
            "signal_confidence": round(context.signal_confidence, 2),
            "alligator": {
                "W1": serialize_alligator(context.alligator_w1),
                "D1": serialize_alligator(context.alligator_d1),
                "H4": serialize_alligator(context.alligator_h4)
            },
            "levels": {
                "nearest_resistance": serialize_fractal(context.nearest_resistance),
                "nearest_support": serialize_fractal(context.nearest_support)
            }
        }
    except Exception as e:
        logging.error(f"Failed to get technical context: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# UTILS & EXPORT
# ============================================================================

@app.get("/api/v1/coins")
async def get_supported_coins():
    return ["BTC", "ETH", "SOL", "XRP", "DOGE"]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("bybit_options.api.app:app", host="0.0.0.0", port=8000, reload=True)
