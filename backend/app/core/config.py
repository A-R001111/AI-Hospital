"""
================================================================================
تنظیمات و کانفیگ اپلیکیشن - نسخه آفلاین
================================================================================
این نسخه بدون نیاز به OpenAI API Key است
================================================================================
"""

import secrets
from typing import List, Optional
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """کلاس تنظیمات اپلیکیشن - نسخه آفلاین"""
    
    # ========================================
    # Application
    # ========================================
    APP_NAME: str = Field(
        default="سامانه گزارش‌نویسی پرستاران",
        description="نام اپلیکیشن"
    )
    APP_VERSION: str = Field(default="1.0.0")
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=False)
    
    # ========================================
    # Server
    # ========================================
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000, ge=1000, le=65535)
    WORKERS: int = Field(default=4, ge=1, le=32)
    
    # ========================================
    # Database
    # ========================================
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://hospitaluser:hospitalpass@localhost:5432/hospital_reports",
        description="آدرس دیتابیس"
    )
    DATABASE_POOL_SIZE: int = Field(default=20, ge=5, le=100)
    DATABASE_MAX_OVERFLOW: int = Field(default=10, ge=0, le=50)
    DATABASE_ECHO: bool = Field(default=False)
    
    # ========================================
    # Security
    # ========================================
    SECRET_KEY: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        min_length=32
    )
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, ge=5, le=1440)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, ge=1, le=30)
    
    # ========================================
    # CORS
    # ========================================
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:8000"
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True)
    CORS_ALLOW_METHODS: str = Field(default="*")
    CORS_ALLOW_HEADERS: str = Field(default="*")
    
    # ========================================
    # Whisper آفلاین (بدون نیاز به API Key!)
    # ========================================
    WHISPER_MODEL_SIZE: str = Field(
        default="base",
        description="سایز مدل Whisper: tiny, base, small, medium, large"
    )
    WHISPER_DEVICE: str = Field(
        default="cpu",
        description="دستگاه: cpu یا cuda (GPU)"
    )
    
    # ========================================
    # Redis
    # ========================================
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379, ge=1, le=65535)
    REDIS_DB: int = Field(default=0, ge=0, le=15)
    REDIS_PASSWORD: Optional[str] = Field(default=None)
    REDIS_DECODE_RESPONSES: bool = Field(default=True)
    
    # ========================================
    # File Upload
    # ========================================
    MAX_UPLOAD_SIZE: int = Field(default=10485760, ge=1048576, le=104857600)
    ALLOWED_AUDIO_FORMATS: str = Field(default="wav,mp3,m4a,ogg,webm,flac")
    UPLOAD_DIR: str = Field(default="uploads/audio")
    
    # ========================================
    # Rate Limiting
    # ========================================
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, ge=10, le=1000)
    RATE_LIMIT_PER_HOUR: int = Field(default=1000, ge=100, le=10000)
    
    # ========================================
    # Logging
    # ========================================
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FILE: str = Field(default="logs/app.log")
    LOG_FORMAT: str = Field(default="json")
    
    # ========================================
    # Validators
    # ========================================
    
    @field_validator("CORS_ORIGINS")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @field_validator("ALLOWED_AUDIO_FORMATS")
    @classmethod
    def parse_audio_formats(cls, v):
        if isinstance(v, str):
            return [fmt.strip().lower() for fmt in v.split(",")]
        return v
    
    @field_validator("CORS_ALLOW_METHODS")
    @classmethod
    def parse_allow_methods(cls, v):
        if v == "*":
            return ["*"]
        if isinstance(v, str):
            return [method.strip().upper() for method in v.split(",")]
        return v
    
    @field_validator("CORS_ALLOW_HEADERS")
    @classmethod
    def parse_allow_headers(cls, v):
        if v == "*":
            return ["*"]
        if isinstance(v, str):
            return [header.strip() for header in v.split(",")]
        return v
    
    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v):
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT باید یکی از {allowed} باشد")
        return v
    
    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v):
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed:
            raise ValueError(f"LOG_LEVEL باید یکی از {allowed} باشد")
        return v.upper()
    
    @field_validator("WHISPER_MODEL_SIZE")
    @classmethod
    def validate_whisper_model(cls, v):
        allowed = ["tiny", "base", "small", "medium", "large"]
        if v not in allowed:
            raise ValueError(f"WHISPER_MODEL_SIZE باید یکی از {allowed} باشد")
        return v
    
    # ========================================
    # Properties
    # ========================================
    
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"
    
    @property
    def database_url_str(self) -> str:
        return str(self.DATABASE_URL)
    
    # ========================================
    # Config
    # ========================================
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """دریافت تنظیمات (با cache)"""
    return Settings()


# ========================================
# Export
# ========================================
settings = get_settings()

__all__ = ["Settings", "settings", "get_settings"]
