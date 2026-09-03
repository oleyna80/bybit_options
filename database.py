"""
Database connection and session management
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in .env file")

# Convert to async URL for asyncpg
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Create async engine
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False,
    poolclass=NullPool,
    pool_pre_ping=True
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

from bybit_options.storage.repositories import (
    OrderRepository,
    PortfolioSnapshotRepository,
    TradeRepository,
)


def get_trade_repository() -> TradeRepository:
    """Get a TradeRepository backed by the configured SQLAlchemy session."""
    from bybit_options.storage.adapters import SQLAlchemyTradeRepository

    return SQLAlchemyTradeRepository(AsyncSessionLocal)


def get_order_repository() -> OrderRepository:
    """Get an OrderRepository backed by the configured SQLAlchemy session."""
    from bybit_options.storage.adapters import SQLAlchemyOrderRepository

    return SQLAlchemyOrderRepository(AsyncSessionLocal)


def get_portfolio_snapshot_repository() -> PortfolioSnapshotRepository:
    """Get a PortfolioSnapshotRepository backed by the configured SQLAlchemy session."""
    from bybit_options.storage.adapters import SQLAlchemyPortfolioSnapshotRepository

    return SQLAlchemyPortfolioSnapshotRepository(AsyncSessionLocal)

# Base class for ORM models
Base = declarative_base()

# Dependency for FastAPI (if needed later)
async def get_db():
    """Get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()

# Test connection function
async def test_connection():
    """Test database connection"""
    from sqlalchemy import text
    try:
        async with async_engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            logger.success("Database connection successful!")
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

async def init_db():
    """Initialize database connection (tables already exist from backfill)"""
    try:
        await test_connection()
        logger.info("✅ Database initialized and ready")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_connection())
