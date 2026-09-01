import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
# Load env vars BEFORE importing database config
load_dotenv()

from bybit_options.services.delta.database_config import db

async def main():
    print("Connecting to database...")
    await db.connect()
    
    migration_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "database_migrations",
        "014_amm_dynamic_params.sql"
    )
    
    print(f"Reading migration file: {migration_file}")
    with open(migration_file, "r") as f:
        sql = f.read()
        
    print("Applying migration...")
    try:
        # Split by statements if necessary, but asyncpg execute() usually handles scripts if supported
        # or we might need to use executescript if it were sqlite, but here it is postgres.
        # asyncpg conn.execute can execute multiple statements separated by semicolons usually.
        await db.execute(sql)
        print("✅ Migration applied successfully.")
    except Exception as e:
        print(f"❌ Migration failed: {e}")
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(main())
