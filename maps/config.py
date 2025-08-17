"""Configuration management for ETA Watcher."""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    google_maps_api_key: str = Field(..., env="GOOGLE_MAPS_API_KEY")
    polling_interval_seconds: int = Field(default=300, env="POLLING_INTERVAL_SECONDS")  # 5 minutes
    default_timeout_minutes: int = Field(default=120, env="DEFAULT_TIMEOUT_MINUTES")  # 2 hours
    max_concurrent_sessions: int = Field(default=10, env="MAX_CONCURRENT_SESSIONS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    """Get application settings singleton."""
    return Settings()