"""
Configuration management using Pydantic Settings
Centralizes all environment variables and app settings
"""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator


class BybitConfig(BaseSettings):
    """Bybit API configuration"""
    
    api_key: str = Field(
        ...,
        description="Bybit API Key"
    )
    
    api_secret: str = Field(
        ...,
        description="Bybit API Secret"
    )
    
    testnet: bool = Field(
        default=False,
        description="Use Bybit testnet"
    )
    
    rate_limit: int = Field(
        default=50,
        description="Max requests per second",
        ge=1,
        le=100
    )
    
    @property
    def base_url(self) -> str:
        """Get appropriate base URL"""
        if self.testnet:
            return "https://api-testnet.bybit.com"
        return "https://api.bybit.com"


class AnalysisConfig(BaseSettings):
    """Analysis settings"""
    
    fetch_enhanced_metrics: bool = Field(
        default=True,
        description="Fetch IV, slippage, and gamma rent"
    )
    
    gamma_rent_threshold: float = Field(
        default=1e-10,
        description="Minimum gamma for rent calculation"
    )
    
    high_gamma_threshold: float = Field(
        default=0.01,
        description="Gamma threshold for warnings"
    )
    
    high_vega_threshold: float = Field(
        default=1000.0,
        description="Vega threshold for warnings (USD)"
    )
    
    high_theta_threshold: float = Field(
        default=100.0,
        description="Theta threshold for warnings (USD/day)"
    )
    
    margin_warning_threshold: float = Field(
        default=60.0,
        description="Margin utilization % for warnings",
        ge=0,
        le=100
    )
    
    margin_critical_threshold: float = Field(
        default=80.0,
        description="Margin utilization % for critical warnings",
        ge=0,
        le=100
    )


class AppConfig(BaseSettings):
    """Application configuration"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Environment
    environment: str = Field(
        default="development",
        description="Application environment"
    )
    
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    
    # Bybit
    bybit_api_key: str = Field(
        ...,
        alias="BYBIT_API_KEY"
    )
    
    bybit_api_secret: str = Field(
        ...,
        alias="BYBIT_API_SECRET"
    )
    
    bybit_testnet: bool = Field(
        default=False,
        alias="BYBIT_TESTNET"
    )
    
    bybit_rate_limit: int = Field(
        default=50,
        alias="BYBIT_RATE_LIMIT"
    )
    
    
    # Database
    database_url: str = Field(
        ...,
        alias="DATABASE_URL",
        description="Database connection URL"
    )

    # API Server (for FastAPI)
    api_host: str = Field(
        default="0.0.0.0",
        description="API server host"
    )
    
    api_port: int = Field(
        default=8000,
        description="API server port",
        ge=1024,
        le=65535
    )
    
    api_workers: int = Field(
        default=1,
        description="Number of API workers",
        ge=1
    )
    
    # CORS
    cors_origins: list[str] = Field(
        default=["*"],
        description="Allowed CORS origins"
    )
    
    # Analysis
    analysis_enhanced_metrics: bool = Field(
        default=True,
        alias="ANALYSIS_ENHANCED_METRICS"
    )
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """Ensure log level is valid"""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(
                f"Invalid log level: {v}. Must be one of {valid_levels}"
            )
        return v_upper
    
    @validator("environment")
    def validate_environment(cls, v):
        """Ensure environment is valid"""
        valid_envs = {"development", "staging", "production"}
        v_lower = v.lower()
        if v_lower not in valid_envs:
            raise ValueError(
                f"Invalid environment: {v}. Must be one of {valid_envs}"
            )
        return v_lower
    
    @property
    def bybit(self) -> BybitConfig:
        """Get Bybit configuration"""
        return BybitConfig(
            api_key=self.bybit_api_key,
            api_secret=self.bybit_api_secret,
            testnet=self.bybit_testnet,
            rate_limit=self.bybit_rate_limit
        )
    
    @property
    def analysis(self) -> AnalysisConfig:
        """Get analysis configuration"""
        return AnalysisConfig(
            fetch_enhanced_metrics=self.analysis_enhanced_metrics
        )
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment == "development"


# Singleton config instance
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """
    Get application configuration
    
    Usage:
        from config import get_config
        
        config = get_config()
        print(config.bybit.api_key)
    """
    global _config
    
    if _config is None:
        _config = AppConfig()
    
    return _config


def reload_config():
    """Force reload configuration from environment"""
    global _config
    _config = None
    return get_config()


# Example usage in other modules:
"""
# In bybit_connector.py
from config import get_config

config = get_config()
connector = BybitConnector(
    api_key=config.bybit.api_key,
    api_secret=config.bybit.api_secret,
    testnet=config.bybit.testnet
)

# In main.py
from config import get_config

config = get_config()
setup_logging(config.log_level)
"""