import asyncio
import os
import logging
from redis.asyncio import Redis
import asyncpg
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] INFRA: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

async def check_redis():
    """Проверка подключения к Redis (Hot Cache)"""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    logger.info(f"🔌 Checking Redis at {redis_url}...")
    
    try:
        r = Redis.from_url(redis_url, decode_responses=True)
        # 1. Ping
        if not await r.ping():
            raise ConnectionError("Redis ping failed")
        
        # 2. Write/Read Test
        await r.set("infra_test_key", "active")
        val = await r.get("infra_test_key")
        
        if val == "active":
            logger.info("✅ Redis: CONNECTION OK (Write/Read confirmed)")
        else:
            logger.error(f"❌ Redis: Data mismatch (Got {val})")
            
        await r.close()
        return True
    except Exception as e:
        logger.error(f"❌ Redis: FAILED - {e}")
        return False

async def check_postgres():
    """Проверка подключения к TimescaleDB/Postgres"""
    # Парсим URL: postgresql://user:pass@localhost:5432/db
    db_url = os.getenv("DB_URL", "postgresql://quant:secure_password@localhost:5432/bybit_data")
    logger.info(f"🔌 Checking Database...")
    
    try:
        # Подключаемся через asyncpg
        conn = await asyncpg.connect(db_url)
        
        # 1. Проверка версии
        version = await conn.fetchval("SELECT version()")
        logger.info(f"   Database: {version.split()[0]} {version.split()[1]}")
        
        # 2. Проверка TimescaleDB (если установлено)
        try:
            ts_version = await conn.fetchval("SELECT extversion FROM pg_extension WHERE extname='timescaledb'")
            logger.info(f"   TimescaleDB Extension: v{ts_version}")
        except Exception:
            logger.warning("   ⚠️ TimescaleDB extension not found (Standard Postgres?)")

        # 3. Тестовая таблица
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS infra_test (
                id SERIAL PRIMARY KEY,
                ts TIMESTAMPTZ DEFAULT NOW(),
                msg TEXT
            )
        """)
        await conn.execute("INSERT INTO infra_test (msg) VALUES ($1)", 'system_check')
        result = await conn.fetchval("SELECT msg FROM infra_test ORDER BY id DESC LIMIT 1")
        
        if result == 'system_check':
            logger.info("✅ Database: CONNECTION OK (Write/Read confirmed)")
        
        # Очистка
        await conn.execute("DROP TABLE infra_test")
        await conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Database: FAILED - {e}")
        return False

async def main():
    load_dotenv()
    print("="*50)
    print("🚀 STARTING INFRASTRUCTURE HEALTH CHECK")
    print("="*50)
    
    redis_ok = await check_redis()
    db_ok = await check_postgres()
    
    print("-" * 50)
    if redis_ok and db_ok:
        print("🟢 SYSTEM READY. All systems operational.")
        exit(0)
    else:
        print("🔴 SYSTEM FAILURE. Check Docker logs.")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())