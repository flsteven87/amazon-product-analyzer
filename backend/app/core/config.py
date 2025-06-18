"""
Core configuration settings for the Amazon Product Analyzer application.

This module handles all environment variables and application settings using
Pydantic Settings for type safety and validation.
"""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All settings are validated using Pydantic and can be overridden
    via environment variables or .env file.
    """
    
    # Application Settings
    app_name: str = Field(default="Amazon Product Analyzer", description="Application name")
    debug: bool = Field(default=True, description="Enable debug mode")
    environment: str = Field(default="development", description="Environment (development/production)")
    secret_key: str = Field(default="dev-secret-key-change-in-production-12345678901234567890", description="Secret key for JWT and other cryptographic operations")
    
    # Database Configuration (使用 SQLite 進行 POC)
    database_url: str = Field(default="sqlite+aiosqlite:///./amazon_analyzer.db", description="Database URL")
    database_echo: bool = Field(default=False, description="Enable SQLAlchemy query logging")
    
    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379", description="Redis connection URL")
    redis_max_connections: int = Field(default=10, description="Maximum Redis connections")
    
    # AI Service Configuration
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")
    
    # Scraping Configuration
    user_agent: str = Field(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        description="User agent for web scraping"
    )
    proxy_url: Optional[str] = Field(default=None, description="Proxy URL for scraping")
    scraping_delay: float = Field(default=1.0, description="Delay between scraping requests (seconds)")
    max_concurrent_requests: int = Field(default=5, description="Maximum concurrent scraping requests")
    
    # API Configuration
    api_v1_prefix: str = Field(default="/api/v1", description="API version 1 prefix")
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins"
    )
    
    # Rate Limiting
    rate_limit_requests: int = Field(default=100, description="Requests per minute limit")
    rate_limit_window: int = Field(default=60, description="Rate limit window in seconds")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings() 