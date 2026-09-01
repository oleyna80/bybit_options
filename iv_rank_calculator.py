import logging
from datetime import datetime, timedelta
from typing import List, Optional

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Float, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy_utils import database_exists, create_database

from config import get_config
from bybit_options.models import PerpetualOHLCV, OptionIVDaily, IVRankDaily

logger = logging.getLogger(__name__)

# --- SQLAlchemy Setup (assuming standard ORM setup) ---

# Use Base from the main project if available, otherwise define one
Base = declarative_base()

class PerpetualOHLCV_DB(Base):
    """Historical daily OHLCV data for Perpetual Futures (e.g., BTC-PERPETUAL)"""
    __tablename__ = 'perpetual_ohlcv'
    
    timestamp = Column(DateTime, primary_key=True) # Hypertable key
    symbol = Column(String, primary_key=True, default='BTC-PERPETUAL')
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    
class OptionIVDaily_DB(Base):
    """Historical daily IV snapshot for ATM monthly option"""
    __tablename__ = 'option_iv_daily'
    
    timestamp = Column(DateTime, primary_key=True) # Hypertable key
    coin = Column(String, primary_key=True, default='BTC')
    atm_strike = Column(Float, nullable=False)
    iv_value = Column(Float, nullable=False)
    days_to_expiry = Column(Integer, nullable=False)

class IVRankDaily_DB(Base):
    """Daily calculated IV Rank (0-100) based on 30-day rolling window"""
    __tablename__ = 'iv_rank_daily'
    
    timestamp = Column(DateTime, primary_key=True) # Hypertable key
    coin = Column(String, primary_key=True, default='BTC')
    iv_rank = Column(Float, nullable=False)
    current_iv = Column(Float, nullable=False)
    min_iv_30d = Column(Float, nullable=False)
    max_iv_30d = Column(Float, nullable=False)
    
# --- Database Manager ---

class DatabaseManager:
    """Handles DB connection, schema creation, and TimescaleDB extension enabling"""
    
    def __init__(self):
        config = get_config()
        self.engine = create_engine(config.database_url)
        self.Session = sessionmaker(bind=self.engine)
        
    def init_db(self):
        """Initializes database and tables, ensuring TimescaleDB is active"""
        # NOTE: This requires sqlalchemy_utils to check for database existence.
        # It's a common pattern in Python projects but might need to be verified
        # if the project has a custom ORM setup. Assuming standard for now.
        
        # NOTE: Init_db is usually called before any connection pooling is set up.
        # In a FastAPI project, it should be called on startup.
        
        if not database_exists(self.engine.url):
            try:
                create_database(self.engine.url)
                logger.info("Database created.")
            except Exception as e:
                # Handle race condition or permission errors when using Docker volume mount
                logger.warning(f"Database creation failed (may already exist/permission error): {e}")

        Base.metadata.create_all(self.engine)
        logger.info("Database tables created/checked.")
        
        self._enable_timescale_extension()
        self._create_hypertables()

    def _enable_timescale_extension(self):
        """Enables the TimescaleDB extension if not already enabled"""
        try:
            with self.Session() as session:
                # Using text for DDL is safer in some setups
                session.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")
                session.commit()
            logger.info("TimescaleDB extension enabled.")
        except Exception as e:
            logger.error(f"Error enabling TimescaleDB extension: {e}")

    def _create_hypertables(self):
        """Converts tables to TimescaleDB hypertables"""
        tables_to_hypertable = {
            'perpetual_ohlcv': 'timestamp',
            'option_iv_daily': 'timestamp',
            'iv_rank_daily': 'timestamp',
        }
        
        try:
            with self.Session() as session:
                for table_name, time_column in tables_to_hypertable.items():
                    # Check if table exists and is not already a hypertable
                    # Note: Using raw SQL with f-strings requires careful security review, 
                    # but is common for internal ORM setup utilities.
                    result = session.execute(f"SELECT * FROM timescaledb_information.hypertables WHERE hypertable_name = '{table_name}';").fetchall()
                    
                    if not result:
                        logger.info(f"Creating hypertable for {table_name} on column {time_column}")
                        # Use SQL expression or text for execution
                        session.execute(f"SELECT create_hypertable('{table_name}', '{time_column}', if_not_exists => TRUE);")
                        session.commit()
                    else:
                        logger.debug(f"Table {table_name} is already a hypertable.")
        except Exception as e:
            logger.error(f"Error creating hypertables: {e}")

# --- IV Rank Calculation Logic ---

class IVRankCalculator:
    """Calculates IV Rank and manages data access for historical metrics."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.Session = db_manager.Session
        
    def calculate_iv_rank(self, iv_history: List[float], lookback_days: int = 30) -> tuple[Optional[float], Optional[float], Optional[float], Optional[float]]:
        """
        Calculates IV Rank (0-100) based on a lookback window.
        
        IV Rank = (Current IV - Min IV) / (Max IV - Min IV) * 100
        Returns: (iv_rank, current_iv, min_iv, max_iv)
        """
        if not iv_history:
            return None, None, None, None

        # Ensure we only use the lookback window
        recent_ivs = iv_history[-lookback_days:]
        
        if len(recent_ivs) < 1:
            return None, None, None, None

        current_iv = recent_ivs[-1]
        
        # Calculate min and max over the window
        min_iv = min(recent_ivs)
        max_iv = max(recent_ivs)
        
        iv_range = max_iv - min_iv
        
        if iv_range < 1e-6:
            # Range is too small, IV Rank is undefined (or 50 if IV is constant)
            return 50.0, current_iv, min_iv, max_iv
            
        iv_rank = ((current_iv - min_iv) / iv_range) * 100
        
        # Clamp to [0, 100]
        iv_rank = max(0.0, min(100.0, iv_rank))
        
        return iv_rank, current_iv, min_iv, max_iv
    
    def get_iv_history(self, coin: str = 'BTC', days: int = 1825) -> List[OptionIVDaily]:
        """Fetches historical IV data from the database."""
        # For a full implementation, this would query the DB using session
        # For now, return mock data
        
        # NOTE: MOCK DATA USES numpy, ensure it's in requirements.txt
        return [
            OptionIVDaily(timestamp=datetime.now() - timedelta(days=i), atm_strike=50000, iv_value=0.5 + 0.2 * np.sin(i / 10), days_to_expiry=30)
            for i in range(days, 0, -1)
        ]

    def get_price_history(self, symbol: str = 'BTC-PERPETUAL', days: int = 1825) -> List[PerpetualOHLCV]:
        """Fetches historical price data (OHLCV) from the database."""
        # For a full implementation, this would query the DB
        # For now, return mock data
        return [
            PerpetualOHLCV(
                timestamp=datetime.now() - timedelta(days=i), 
                open=50000 + 1000 * np.cos(i / 20), 
                high=50500 + 1000 * np.cos(i / 20),
                low=49500 + 1000 * np.cos(i / 20),
                close=50000 + 1000 * np.cos(i / 20),
                volume=1000
            )
            for i in range(days, 0, -1)
        ]

    def save_iv_rank(self, iv_rank_model: IVRankDaily):
        """Saves a calculated IV Rank to the database."""
        logger.info(f"Saving IV Rank for {iv_rank_model.timestamp}: {iv_rank_model.iv_rank:.2f}")
        # Full implementation would use session.merge(IVRankDaily_DB(**iv_rank_model.model_dump()))

    def run_daily_calculation(self):
        """Placeholder for the daily cron job logic."""
        logger.info("Starting daily IV Rank calculation...")
        
        # 1. Fetch IV history (e.g., last 30 days + today)
        iv_data = self.get_iv_history(days=30) # Only fetch necessary data
        iv_values = [d.iv_value for d in iv_data]
        
        # 2. Calculate IV Rank (30-day window is handled inside the function)
        iv_rank, current_iv, min_iv, max_iv = self.calculate_iv_rank(iv_values, lookback_days=30)

        if iv_rank is not None:
            # 3. Create model and save
            rank_model = IVRankDaily(
                timestamp=datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0),
                iv_rank=iv_rank,
                current_iv=current_iv,
                min_iv_30d=min_iv,
                max_iv_30d=max_iv
            )
            self.save_iv_rank(rank_model)
            logger.info(f"Daily IV Rank calculated and saved: {iv_rank:.2f}")
        else:
            logger.warning("Could not calculate IV Rank: Insufficient data.")

# --- Singleton Instantiation ---

# Instantiate the DB Manager once
db_manager = DatabaseManager()
iv_rank_calculator = IVRankCalculator(db_manager)

def get_db_manager() -> DatabaseManager:
    return db_manager

def get_iv_rank_calculator() -> IVRankCalculator:
    return iv_rank_calculator

def init_db_on_startup():
    """Initializes the database and ensures TimescaleDB setup"""
    db_manager.init_db()