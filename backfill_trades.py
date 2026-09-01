"""
Backfill historical trades from Bybit to database
"""
import asyncio
import json
from datetime import datetime, timezone
from typing import List, Dict, Any
from sqlalchemy import select
from database import AsyncSessionLocal
from trade_logger import Trade


async def parse_bybit_trade(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Convert Bybit API format to our DB format"""
    
    # Parse timestamp
    exec_time_ms = int(raw.get("execTime", 0))
    timestamp = datetime.fromtimestamp(exec_time_ms / 1000, tz=timezone.utc)
    
    # Convert IV from string to float (as fraction)
    def parse_iv(iv_str):
        if not iv_str or iv_str == "0":
            return None
        iv = float(iv_str)
        # If > 1, assume it's percentage, convert to fraction
        return iv / 100 if iv > 1 else iv
    
    return {
        # Primary fields
        "exec_id": raw.get("execId"),
        "timestamp": timestamp,
        "symbol": raw.get("symbol"),
        "side": raw.get("side"),
        "size": float(raw.get("execQty", 0)),
        "exec_price": float(raw.get("execPrice", 0)),
        "fee": float(raw.get("execFee", 0)),
        "role": "Maker" if raw.get("isMaker") else "Taker",
        
        # Original fields
        "iv": parse_iv(raw.get("markIv")),  # Mark IV at execution
        "underlying_price": float(raw.get("underlyingPrice", 0)) if raw.get("underlyingPrice") else None,
        "strategy_tag": None,  # Will be filled manually later
        
        # NEW: Order tracking
        "order_id": raw.get("orderId"),
        "order_link_id": raw.get("orderLinkId"),
        "order_type": raw.get("orderType"),
        "stop_order_type": raw.get("stopOrderType"),
        
        # NEW: Pricing
        "mark_price": float(raw.get("markPrice", 0)) if raw.get("markPrice") else None,
        "mark_iv": parse_iv(raw.get("markIv")),
        "index_price": float(raw.get("indexPrice", 0)) if raw.get("indexPrice") else None,
        "trade_iv": parse_iv(raw.get("tradeIv")),
        
        # NEW: Execution details
        "exec_value": float(raw.get("execValue", 0)) if raw.get("execValue") else None,
        "closed_size": float(raw.get("closedSize", 0)) if raw.get("closedSize") else None,
        "order_qty": float(raw.get("orderQty", 0)) if raw.get("orderQty") else None,
        "order_price": float(raw.get("orderPrice", 0)) if raw.get("orderPrice") else None,
        "leaves_qty": float(raw.get("leavesQty", 0)) if raw.get("leavesQty") else None,
        
        # NEW: Fees
        "fee_rate": float(raw.get("feeRate", 0)) if raw.get("feeRate") else None,
        "fee_currency": raw.get("feeCurrency"),
        "exec_fee_v2": float(raw.get("execFeeV2", 0)) if raw.get("execFeeV2") else None,
        "extra_fees": raw.get("extraFees"),
        
        # NEW: Other
        "block_trade_id": raw.get("blockTradeId"),
        "seq": int(raw.get("seq", 0)) if raw.get("seq") else None,
        "market_unit": raw.get("marketUnit"),
    }


async def load_trades_from_json(filepath: str) -> List[Dict[str, Any]]:
    """Load trades from JSON file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        raw_trades = json.load(f)
    
    print(f"📄 Загружено {len(raw_trades)} сделок из {filepath}")
    
    # Parse all trades
    parsed = []
    for raw in raw_trades:
        try:
            trade = await parse_bybit_trade(raw)
            parsed.append(trade)
        except Exception as e:
            print(f"⚠️ Ошибка парсинга сделки {raw.get('execId')}: {e}")
    
    return parsed


async def check_existing_exec_ids(exec_ids: List[str]) -> set:
    """Check which exec_ids already exist in DB"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Trade.exec_id).where(Trade.exec_id.in_(exec_ids))
        )
        existing = {row[0] for row in result.fetchall()}
    
    print(f"🔍 Найдено в БД: {len(existing)} из {len(exec_ids)}")
    return existing


async def insert_trades_batch(trades: List[Dict[str, Any]], batch_size: int = 100):
    """Insert trades in batches with deduplication"""
    
    # Get existing IDs
    exec_ids = [t["exec_id"] for t in trades]
    existing_ids = await check_existing_exec_ids(exec_ids)
    
    # Filter out duplicates
    new_trades = [t for t in trades if t["exec_id"] not in existing_ids]
    
    if not new_trades:
        print("✅ Все сделки уже есть в БД")
        return
    
    print(f"💾 Загружаем {len(new_trades)} новых сделок...")
    
    async with AsyncSessionLocal() as session:
        for i in range(0, len(new_trades), batch_size):
            batch = new_trades[i:i+batch_size]
            
            for trade_data in batch:
                trade = Trade(**trade_data)
                session.add(trade)
            
            await session.commit()
            print(f"  ✓ Batch {i//batch_size + 1}: {len(batch)} сделок")
    
    print(f"✅ Загружено {len(new_trades)} новых сделок")


async def main():
    """Main backfill function"""
    print("🚀 Начинаем загрузку истории сделок\n")
    
    # 1. Load from JSON file (created by your trade_history.py)
    filepath = "bybit_option_fills_year.json"
    trades = await load_trades_from_json(filepath)
    
    # 2. Insert into database
    await insert_trades_batch(trades)
    
    print("\n🎉 Backfill завершен!")


if __name__ == "__main__":
    asyncio.run(main())
