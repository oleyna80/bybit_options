"""
Delta Hedger Bot - Configuration Loader

Загрузчик конфигурации из .env и/или базы данных.
"""

import os
from typing import Optional

from .models import HedgerConfig, HedgerMode


class HedgerConfigLoader:
    """
    Загрузчик конфигурации для Delta Hedger Bot.
    
    Поддерживает загрузку из:
    - Переменных окружения (.env)
    - Базы данных (таблица hedger_config)
    """
    
    # Префикс для переменных окружения
    ENV_PREFIX = "HEDGER_"
    
    # Маппинг переменных окружения на поля конфига
    ENV_MAPPING = {
        "HEDGER_MODE": "mode",
        "HEDGER_TARGET_DELTA": "target_delta",
        "HEDGER_THRESHOLD": "threshold",
        "HEDGER_DIRECTIONAL_BIAS_LONG": "directional_bias_long",
        "HEDGER_DIRECTIONAL_BIAS_SHORT": "directional_bias_short",
        "HEDGER_ENABLED": "enabled",
        "HEDGER_CHECK_INTERVAL": "check_interval_seconds",
        "HEDGER_MAX_ORDER_SIZE": "max_order_size",
        "HEDGER_LIMIT_PRICE_OFFSET_BPS": "limit_price_offset_bps",
        "HEDGER_MAX_OPTION_SIZE": "max_option_size",
    }
    
    @classmethod
    def load_from_env(cls) -> HedgerConfig:
        """
        Загружает конфигурацию из переменных окружения.
        
        Использует значения по умолчанию для отсутствующих переменных.
        
        Returns:
            HedgerConfig с загруженными значениями
            
        Example:
            # .env file:
            HEDGER_MODE=NEUTRAL
            HEDGER_THRESHOLD=0.003
            HEDGER_ENABLED=true
        """
        config_dict = {}
        
        # Mode (enum)
        mode_str = os.getenv("HEDGER_MODE", "NEUTRAL").upper()
        try:
            config_dict["mode"] = HedgerMode(mode_str)
        except ValueError:
            config_dict["mode"] = HedgerMode.NEUTRAL
        
        # Float values
        float_fields = [
            ("HEDGER_TARGET_DELTA", "target_delta", 0.0),
            ("HEDGER_THRESHOLD", "threshold", 0.003),
            ("HEDGER_DIRECTIONAL_BIAS_LONG", "directional_bias_long", 0.01),
            ("HEDGER_DIRECTIONAL_BIAS_SHORT", "directional_bias_short", -0.01),
            ("HEDGER_MAX_ORDER_SIZE", "max_order_size", 0.1),
            ("HEDGER_MAX_OPTION_SIZE", "max_option_size", 0.5),
        ]
        
        for env_name, field_name, default in float_fields:
            value = os.getenv(env_name)
            if value is not None:
                try:
                    config_dict[field_name] = float(value)
                except ValueError:
                    config_dict[field_name] = default
            else:
                config_dict[field_name] = default
        
        # Integer values
        int_fields = [
            ("HEDGER_CHECK_INTERVAL", "check_interval_seconds", 60),
            ("HEDGER_LIMIT_PRICE_OFFSET_BPS", "limit_price_offset_bps", 5),
        ]
        
        for env_name, field_name, default in int_fields:
            value = os.getenv(env_name)
            if value is not None:
                try:
                    config_dict[field_name] = int(value)
                except ValueError:
                    config_dict[field_name] = default
            else:
                config_dict[field_name] = default
        
        # Boolean values
        enabled_str = os.getenv("HEDGER_ENABLED", "false").lower()
        config_dict["enabled"] = enabled_str in ("true", "1", "yes", "on")
        
        return HedgerConfig(**config_dict)
    
    @classmethod
    async def load_from_db(
        cls, 
        pool,  # asyncpg.Pool
        override_env: bool = True
    ) -> HedgerConfig:
        """
        Загружает конфигурацию из таблицы hedger_config.
        
        Args:
            pool: asyncpg connection pool
            override_env: Если True, значения из БД перезаписывают .env
            
        Returns:
            HedgerConfig с загруженными значениями
        """
        # Начинаем с env конфига
        if override_env:
            config_dict = cls.load_from_env().model_dump()
        else:
            config_dict = {}
        
        # Загружаем из БД
        query = "SELECT key, value FROM hedger_config"
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query)
        
        # Маппинг ключей БД на поля конфига
        db_mapping = {
            "mode": ("mode", lambda x: HedgerMode(x.upper())),
            "target_delta": ("target_delta", float),
            "threshold": ("threshold", float),
            "directional_bias_long": ("directional_bias_long", float),
            "directional_bias_short": ("directional_bias_short", float),
            "enabled": ("enabled", lambda x: x.lower() in ("true", "1")),
            "check_interval_seconds": ("check_interval_seconds", int),
            "max_order_size": ("max_order_size", float),
            "limit_price_offset_bps": ("limit_price_offset_bps", int),
            "max_option_size": ("max_option_size", float),
        }
        
        for row in rows:
            key = row["key"]
            value = row["value"]
            
            if key in db_mapping:
                field_name, converter = db_mapping[key]
                try:
                    config_dict[field_name] = converter(value)
                except (ValueError, KeyError):
                    pass  # Keep existing value
        
        return HedgerConfig(**config_dict)
    
    @classmethod
    async def save_to_db(cls, pool, config: HedgerConfig) -> None:
        """
        Сохраняет конфигурацию в таблицу hedger_config.
        
        Args:
            pool: asyncpg connection pool
            config: Конфигурация для сохранения
        """
        config_dict = config.model_dump()
        
        # Преобразуем значения в строки
        values = []
        for key, value in config_dict.items():
            if isinstance(value, HedgerMode):
                str_value = value.value
            elif isinstance(value, bool):
                str_value = "true" if value else "false"
            else:
                str_value = str(value)
            values.append((key, str_value))
        
        query = """
            INSERT INTO hedger_config (key, value, updated_at)
            VALUES ($1, $2, NOW())
            ON CONFLICT (key) DO UPDATE
            SET value = EXCLUDED.value, updated_at = NOW()
        """
        
        async with pool.acquire() as conn:
            await conn.executemany(query, values)


def get_default_config() -> HedgerConfig:
    """
    Возвращает конфигурацию по умолчанию.
    
    Используется для инициализации или тестирования.
    """
    return HedgerConfig(
        mode=HedgerMode.NEUTRAL,
        target_delta=0.0,
        threshold=0.003,
        directional_bias_long=0.01,
        directional_bias_short=-0.01,
        enabled=False,
        check_interval_seconds=60,
        max_order_size=0.1,
        limit_price_offset_bps=5,
        max_option_size=0.5,
    )
