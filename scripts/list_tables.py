import asyncio
import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

async def list_tables():
    host = os.getenv('DELTA_DB_HOST', 'localhost')
    port = os.getenv('DELTA_DB_PORT', '5432')
    user = os.getenv('DELTA_DB_USER', 'trading_user')
    password = os.getenv('DELTA_DB_PASSWORD', '')
    database = os.getenv('DELTA_DB_NAME', 'delta_analytics_db')

    print(f"Connecting to {database} at {host}:{port} as {user}...")

    try:
        conn = await asyncpg.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        
        print("\nExisting tables:")
        rows = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        for row in rows:
            print(f"- {row['table_name']}")
            
        await conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(list_tables())
