import asyncio
import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

async def diagnose_portfolio_v2():
    host = os.getenv('DELTA_DB_HOST', 'localhost')
    port = os.getenv('DELTA_DB_PORT', '5432')
    user = os.getenv('DELTA_DB_USER', 'trading_user')
    password = os.getenv('DELTA_DB_PASSWORD', '')
    database = os.getenv('DELTA_DB_NAME', 'delta_analytics_db')

    print(f"Connecting to {database}...")
    try:
        conn = await asyncpg.connect(host=host, port=port, user=user, password=password, database=database)
        
        # 1. Check amm_legs (Strategy Positions)
        print("\n[AMM LEGS (amm_legs table)]")
        rows = await conn.fetch("""
            SELECT l.id, l.symbol, l.side, l.total_filled, s.name 
            FROM amm_legs l
            JOIN amm_strategies s ON l.strategy_id = s.id
            WHERE s.is_active = true
        """)
        if not rows:
            print("No active AMM legs found.")
        else:
            for r in rows:
                print(f" - Leg #{r['id']} {r['symbol']} ({r['side']}): Filled={r['total_filled']} (Strategy: {r['name']})")

        # 2. Check position_entries (If explicit positions exist)
        print("\n[POSITION ENTRIES (position_entries table)]")
        # Check if table exists first
        exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'position_entries'
            );
        """)
        
        if exists:
            rows = await conn.fetch("SELECT * FROM position_entries LIMIT 5")
            if not rows:
                print("Table 'position_entries' exists but is empty.")
            else:
                for r in rows:
                    print(r)
        else:
            print("Table 'position_entries' does NOT exist.")

        await conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(diagnose_portfolio_v2())
