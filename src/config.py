"""Configuration management for the application."""

import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Keys
    google_api_key: Optional[str] = Field(default=None, alias="GOOGLE_API_KEY")
    
    # Model Configuration
    model_name: str = Field(default="gemini-1.5-flash", alias="MODEL_NAME")
    temperature: float = Field(default=0.3, alias="TEMPERATURE")
    max_tokens: int = Field(default=1024, alias="MAX_TOKENS")
    
    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    
    # MCP Server
    mcp_server_host: str = Field(default="localhost", alias="MCP_SERVER_HOST")
    mcp_server_port: int = Field(default=8000, alias="MCP_SERVER_PORT")
    
    # Paths
    data_dir: Path = Field(default=Path("data"))
    
    # Security
    max_verification_attempts: int = Field(default=3)
    session_timeout_minutes: int = Field(default=30)
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }
    
    @property
    def customers_path(self) -> Path:
        return self.data_dir / "customers.csv"
    
    @property
    def orders_path(self) -> Path:
        return self.data_dir / "orders.csv"
    
    @property
    def refund_policies_path(self) -> Path:
        return self.data_dir / "refund_policies.json"
    
    @property
    def tickets_path(self) -> Path:
        return self.data_dir / "support_tickets.csv"


# Global settings instance
settings = Settings()
