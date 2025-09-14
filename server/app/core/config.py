"""
Application configuration settings.
"""
import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "AI Chat Application"

    # CORS Configuration
    CORS_ORIGINS: str = "http://localhost:3000,https://fitgpt-gamma.vercel.app"

    # Supabase Configuration
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_KEY: str = ""

    # AI API Keys
    GEMINI_API_KEY: str = ""

    # File Configuration
    MAX_FILE_SIZE: int = 26214400  # 25MB
    ALLOWED_FILE_TYPES: List[str] = ["application/pdf"]

    # Model Configuration
    GEMINI_MODEL: str = "gemini-2.0-flash-exp"
    EMBEDDING_MODEL: str = "text-embedding-004"

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def cors_origins_list(self) -> List[str]:
        """Convert CORS_ORIGINS string to list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


settings = Settings()
