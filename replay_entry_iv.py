"""
Replay historical trades to calculate Entry IV for positions.
"""
import asyncio
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, text

from database import AsyncSessionLocal
from trade_logger import Trade, PositionEntry


async def replay_trade(session, trade: Trade) -> None:
    """
    Apply single trade to position_entries table.
    Mirrors trade_logger._update_position_entries logic (simplified).
    """
    symbol = trade.symbol
    side = trade.side
    qty = float(trade.size)
    price = float(trade.exec_price)
    iv = float(trade.mark_iv) if trade.mark_iv else None
    exec_time = trade.timestamp

    # Skip if no IV
    if iv is None or iv == 0:
        print(f"⚠️ Skip {symbol}: No IV data")
        return

    signed_qty = qty if side == "Buy" else -qty

    result = await session.execute(
        select(PositionEntry).where(PositionEntry.symbol == symbol)
    )
    existing = result.scalar_one_or_none()

    if existing:
        old_net_qty = float(existing.net_qty)
        new_net_qty = old_net_qty + signed_qty

        # Position flip across zero
        if (old_net_qty > 0 and new_net_qty < 0) or (old_net_qty < 0 and new_net_qty > 0):
            await session.delete(existing)
            if abs(new_net_qty) > 1e-8:
                new_side = "LONG" if new_net_qty > 0 else "SHORT"
                new_entry = PositionEntry(
                    symbol=symbol,
                    entry_price=price,
                    entry_iv=iv,
                    net_qty=new_net_qty,
                    abs_qty=abs(new_net_qty),
                    entry_time=exec_time,
                    last_update=exec_time,
                    fill_count=1,
                    position_side=new_side,
                    created_at=datetime.now(timezone.utc),
                )
                session.add(new_entry)
                print(f"  🔄 Flip {symbol}: {old_net_qty:.4f}→{new_net_qty:.4f}")

        # Position closed
        elif abs(new_net_qty) < 1e-8:
            await session.delete(existing)
            print(f"  ✖️ Close {symbol}")

        # Position reduced (same direction)
        elif abs(new_net_qty) < abs(old_net_qty):
            existing.net_qty = new_net_qty
            existing.abs_qty = abs(new_net_qty)
            existing.last_update = exec_time
            print(f"  ⬇️ Reduce {symbol}: {old_net_qty:.4f}→{new_net_qty:.4f}")

        # Position increased (weighted average)
        else:
            old_abs_qty = float(existing.abs_qty)
            old_iv = float(existing.entry_iv) if existing.entry_iv else 0
            old_price = float(existing.entry_price)

            new_abs_qty = abs(new_net_qty)
            new_avg_iv = (old_abs_qty * old_iv + qty * iv) / new_abs_qty
            new_avg_price = (old_abs_qty * old_price + qty * price) / new_abs_qty

            existing.net_qty = new_net_qty
            existing.abs_qty = new_abs_qty
            existing.entry_iv = new_avg_iv
            existing.entry_price = new_avg_price
            existing.last_update = exec_time
            existing.fill_count += 1

            print(f"  ⬆️ Increase {symbol}: IV {old_iv*100:.1f}%→{new_avg_iv*100:.1f}%")

    else:
        if abs(signed_qty) > 1e-8:
            position_side = "LONG" if signed_qty > 0 else "SHORT"
            new_entry = PositionEntry(
                symbol=symbol,
                entry_price=price,
                entry_iv=iv,
                net_qty=signed_qty,
                abs_qty=abs(signed_qty),
                entry_time=exec_time,
                last_update=exec_time,
                fill_count=1,
                position_side=position_side,
                created_at=datetime.now(timezone.utc),
            )
            session.add(new_entry)
            print(f"  ➕ New {symbol} {position_side}: qty={signed_qty:.4f} IV={iv*100:.1f}%")


async def main():
    """Replay all trades in chronological order."""
    print("🚀 Начинаем replay истории сделок для Entry IV\n")

    async with AsyncSessionLocal() as session:
        # 1. Clear existing position_entries
        print("🗑️ Очистка старых данных position_entries...")
        await session.execute(text("DELETE FROM position_entries"))
        await session.commit()

        # 2. Load all trades ordered by time
        result = await session.execute(select(Trade).order_by(Trade.timestamp.asc()))
        trades = result.scalars().all()

        print(f"📊 Найдено {len(trades)} сделок для replay\n")

        # 3. Replay each trade
        for i, trade in enumerate(trades, 1):
            print(f"[{i}/{len(trades)}] {trade.timestamp.strftime('%Y-%m-%d %H:%M')} {trade.symbol} {trade.side}")
            await replay_trade(session, trade)
            await session.commit()

        # 4. Show final positions
        result = await session.execute(select(PositionEntry))
        positions = result.scalars().all()

        print(f"\n✅ Replay завершен!")
        print(f"📈 Открытых позиций: {len(positions)}\n")

        if positions:
            print("Текущие позиции с Entry IV:")
            print("-" * 80)
            for pos in positions:
                print(
                    f"{pos.symbol:<25} {pos.position_side:<6} "
                    f"qty={pos.net_qty:>8.4f} "
                    f"Entry IV={pos.entry_iv*100:>6.2f}% "
                    f"Entry Price=${pos.entry_price:>10.2f}"
                )
            print("-" * 80)


if __name__ == "__main__":
    asyncio.run(main())
