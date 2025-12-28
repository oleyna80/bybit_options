"""
FastAPI Integration Example
Demonstrates how to expose the risk engine as REST endpoints

To run:
    pip install fastapi uvicorn
    uvicorn api_example:app --reload --host 0.0.0.0 --port 8000
"""
import os
import logging
from typing import Dict, Optional, List
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, HTTPException, Depends, Query, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession

from bybit_connector import BybitConnector
from analysis_orchestrator import AnalysisOrchestrator
from data_models import (
    PortfolioRiskModel,
    CoinRiskModel,
    MarginModel,
    PriceHistoryResponse,
    IVHistoryResponse,
    IVRankHistoryResponse
)
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

load_dotenv()
logger = logging.getLogger(__name__)

# ============================================================================
# GLOBAL STATE & LIFESPAN
# ============================================================================

_connector: Optional[BybitConnector] = None
_ws_manager: Optional[WebSocketManager] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global _connector, _ws_manager
    
    # 1. Init Bybit Connector
    api_key = os.getenv("BYBIT_API_KEY")
    api_secret = os.getenv("BYBIT_API_SECRET")
    
    if not api_key or not api_secret:
        raise RuntimeError("Missing BYBIT_API_KEY or BYBIT_API_SECRET")
    
    _connector = BybitConnector(api_key=api_key, api_secret=api_secret, testnet=False)
    await _connector._init_session()
    logger.info("✅ Bybit connector initialized")
    
    # 2. Init Database (Ensure tables exist)
    try:
        await init_db_on_startup()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database init failed: {e}")
    
    # 3. Init WebSocket Manager
    _ws_manager = WebSocketManager(broadcast_interval=5.0)
    logger.info("✅ WebSocket manager initialized")
    
    yield
    
    # Cleanup
    if _connector:
        await _connector.close()
    if _ws_manager:
        _ws_manager.stop_broadcast_loop()
    logger.info("🛑 Services stopped")


app = FastAPI(
    title="Bybit Options Risk Engine",
    version="1.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
            
            if "markIv" in position:
                position["current_iv"] = position["markIv"]
        
        return {"count": len(raw_positions), "positions": raw_positions}
    
    except Exception as e:
        logger.error(f"Failed to fetch positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# MARKET DATA & OPTIONS BOARD
# ============================================================================

@app.get("/api/v1/options-board")
async def get_options_board(
    base_coin: str = Query("BTC"),
    expiry: Optional[str] = None,
    option_type: Optional[str] = None,
    sort_by: str = "strike",
    sort_order: str = "asc",
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
            code = "C" if option_type.upper() == "CALL" else "P"
            symbols = [s for s in symbols if s.endswith(f"-{code}")]
        
        # Limit for MVP performance
        symbols = symbols[:50]
        ticker_data = await fetch_option_tickers(_connector, symbols)

        # 5. Format
        formatted = []
        for sym in symbols:
            if sym not in ticker_data: continue
            formatted.append(format_option_display(
                parse_option_symbol(sym), ticker_data[sym], underlying_price
            ))

        return {
            "underlying_price": underlying_price,
            "options": sort_options_for_display(formatted, sort_by, sort_order)
        }
    except Exception as e:
        logger.error(f"Options board error: {e}")
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
# UTILS & EXPORT
# ============================================================================

@app.get("/api/v1/coins")
async def get_supported_coins():
    return ["BTC", "ETH", "SOL", "XRP", "DOGE"]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_example:app", host="0.0.0.0", port=8000, reload=True)
