"""
Database Configuration for Delta Analytics
==========================================
Connection pool для asyncpg с delta_analytics_db.
"""

import asyncpg
import os
from typing import Optional
from loguru import logger


class DatabaseConfig:
    """
    Singleton для управления connection pool к delta_analytics_db.
    
    Usage:
        db = DatabaseConfig()
        await db.connect()
        
        async with db.acquire() as conn:
            await conn.execute("INSERT INTO ...")
        
        await db.close()
    """
    
    _instance: Optional['DatabaseConfig'] = None
    _pool: Optional[asyncpg.Pool] = None
    
    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Инициализация (вызывается только один раз)"""
        if not hasattr(self, 'initialized'):
            self.initialized = True
            
            # Параметры подключения из .env
            self.host = os.getenv('DELTA_DB_HOST', 'localhost')
            self.port = int(os.getenv('DELTA_DB_PORT', '5432'))
            self.user = os.getenv('DELTA_DB_USER', 'trading_user')
            self.password = os.getenv('DELTA_DB_PASSWORD', '')
            self.database = os.getenv('DELTA_DB_NAME', 'delta_analytics_db')
            
            # Connection pool settings
            self.min_size = 5  # Минимум соединений
            self.max_size = 20  # Максимум соединений
    
    async def connect(self):
        """Создать connection pool"""
        if self._pool is None:
            try:
                self._pool = await asyncpg.create_pool(
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    database=self.database,
                    min_size=self.min_size,
                    max_size=self.max_size,
                    command_timeout=60
                )
                logger.info(
                    f"✅ Database pool created: {self.database} "
                    f"({self.min_size}-{self.max_size} connections)"
                )
            except Exception as e:
                logger.error(f"❌ Failed to create database pool: {e}")
                raise
    
    async def close(self):
        """Закрыть connection pool"""
        if self._pool is not None:
            await self._pool.close()
            self._pool = None
            logger.info("Database pool closed")
    
    def acquire(self):
        """
        Получить соединение из pool.
        
        Usage:
            async with db.acquire() as conn:
                await conn.execute("SELECT ...")
        """
        if self._pool is None:
            raise RuntimeError("Database pool not initialized. Call connect() first.")
        
        return self._pool.acquire()
    
    async def execute(self, query: str, *args):
        """
        Выполнить query (для простых операций).
        
        Args:
            query: SQL query
            *args: Query parameters
        
        Returns:
            Result of execute
        """
        async with self.acquire() as conn:
            return await conn.execute(query, *args)
    
    async def fetch(self, query: str, *args):
        """
        Выполнить SELECT query.
        
        Args:
            query: SQL query
            *args: Query parameters
        
        Returns:
            List of records
        """
        async with self.acquire() as conn:
            return await conn.fetch(query, *args)
    
    async def fetchrow(self, query: str, *args):
        """
        Выполнить SELECT query и вернуть одну строку.
        
        Args:
            query: SQL query
            *args: Query parameters
        
        Returns:
            Single record or None
        """
        async with self.acquire() as conn:
            return await conn.fetchrow(query, *args)


# Глобальный экземпляр
db = DatabaseConfig()
