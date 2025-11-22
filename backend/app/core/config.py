"""
================================================================================
تنظیمات و کانفیگ اپلیکیشن
================================================================================
این ماژول تمام تنظیمات اپلیکیشن را از متغیرهای محیطی می‌خواند و
به صورت type-safe در دسترس قرار می‌دهد.

استفاده از Pydantic Settings برای validation و type checking
================================================================================
"""

import secrets
from typing import List, Optional
from functools import lru_cache

from pydantic import Field, validator, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    کلاس تنظیمات اپلیکیشن
    
    تمام تنظیمات از متغیرهای محیطی یا فایل .env خوانده می‌شوند.
    
    Attributes:
        APP_NAME: نام اپلیکیشن
        APP_VERSION: نسخه اپلیکیشن
        ENVIRONMENT: محیط اجرا (development, staging, production)
        DEBUG: حالت دیباگ
    """
    
    # ========================================
    # تنظیمات کلی Application
    # ========================================
    APP_NAME: str = Field(
        default="سامانه گزارش‌نویسی پرستاران",
        description="نام اپلیکیشن"
    )
    APP_VERSION: str = Field(
        default="1.0.0",
        description="نسخه اپلیکیشن"
    )
    ENVIRONMENT: str = Field(
        default="development",
        description="محیط اجرا: development, staging, production"
    )
    DEBUG: bool = Field(
        default=False,
        description="حالت دیباگ (فقط در development True باشد)"
    )
    
    # ========================================
    # تنظیمات Server
    # ========================================
    HOST: str = Field(
        default="0.0.0.0",
        description="آدرس IP برای bind شدن سرور"
    )
    PORT: int = Field(
        default=8000,
        ge=1000,
        le=65535,
        description="پورت سرور"
    )
    WORKERS: int = Field(
        default=4,
        ge=1,
        le=32,
        description="تعداد worker processes"
    )
    
    # ========================================
    # تنظیمات Database
    # ========================================
    DATABASE_URL: PostgresDsn = Field(
        description="آدرس اتصال به دیتابیس PostgreSQL"
    )
    DATABASE_POOL_SIZE: int = Field(
        default=20,
        ge=5,
        le=100,
        description="تعداد connection pool"
    )
    DATABASE_MAX_OVERFLOW: int = Field(
        default=10,
        ge=0,
        le=50,
        description="حداکثر تعداد connection اضافی"
    )
    DATABASE_ECHO: bool = Field(
        default=False,
        description="نمایش SQL queries در لاگ"
    )
    
    # ========================================
    # تنظیمات Security
    # ========================================
    SECRET_KEY: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        min_length=32,
        description="کلید امنیتی برای JWT و رمزنگاری"
    )
    ALGORITHM: str = Field(
        default="HS256",
        description="الگوریتم رمزنگاری JWT"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        ge=5,
        le=1440,
        description="مدت اعتبار access token (دقیقه)"
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7,
        ge=1,
        le=30,
        description="مدت اعتبار refresh token (روز)"
    )
    
    # ========================================
    # تنظیمات CORS
    # ========================================
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="لیست originهای مجاز برای CORS"
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(
        default=True,
        description="اجازه ارسال credentials در CORS"
    )
    CORS_ALLOW_METHODS: List[str] = Field(
        default=["*"],
        description="متدهای HTTP مجاز"
    )
    CORS_ALLOW_HEADERS: List[str] = Field(
        default=["*"],
        description="headerهای مجاز"
    )
    
    # ========================================
    # تنظیمات OpenAI
    # ========================================
    OPENAI_API_KEY: str = Field(
        description="کلید API OpenAI برای Whisper"
    )
    OPENAI_MODEL: str = Field(
        default="whisper-1",
        description="مدل Whisper"
    )
    OPENAI_ORGANIZATION: Optional[str] = Field(
        default=None,
        description="Organization ID در OpenAI (اختیاری)"
    )
    
    # ========================================
    # تنظیمات Redis
    # ========================================
    REDIS_HOST: str = Field(
        default="localhost",
        description="آدرس سرور Redis"
    )
    REDIS_PORT: int = Field(
        default=6379,
        ge=1,
        le=65535,
        description="پورت Redis"
    )
    REDIS_DB: int = Field(
        default=0,
        ge=0,
        le=15,
        description="شماره دیتابیس Redis"
    )
    REDIS_PASSWORD: Optional[str] = Field(
        default=None,
        description="رمز عبور Redis (اختیاری)"
    )
    REDIS_DECODE_RESPONSES: bool = Field(
        default=True,
        description="تبدیل خودکار bytes به string"
    )
    
    # ========================================
    # تنظیمات File Upload
    # ========================================
    MAX_UPLOAD_SIZE: int = Field(
        default=10485760,  # 10MB
        ge=1048576,  # حداقل 1MB
        le=104857600,  # حداکثر 100MB
        description="حداکثر سایز فایل آپلود (bytes)"
    )
    ALLOWED_AUDIO_FORMATS: List[str] = Field(
        default=["wav", "mp3", "m4a", "ogg", "webm"],
        description="فرمت‌های مجاز فایل صوتی"
    )
    UPLOAD_DIR: str = Field(
        default="uploads/audio",
        description="مسیر ذخیره فایل‌های آپلود شده"
    )
    
    # ========================================
    # تنظیمات Rate Limiting
    # ========================================
    RATE_LIMIT_PER_MINUTE: int = Field(
        default=60,
        ge=10,
        le=1000,
        description="حداکثر تعداد درخواست در دقیقه"
    )
    RATE_LIMIT_PER_HOUR: int = Field(
        default=1000,
        ge=100,
        le=10000,
        description="حداکثر تعداد درخواست در ساعت"
    )
    
    # ========================================
    # تنظیمات Logging
    # ========================================
    LOG_LEVEL: str = Field(
        default="INFO",
        description="سطح لاگ: DEBUG, INFO, WARNING, ERROR, CRITICAL"
    )
    LOG_FILE: str = Field(
        default="logs/app.log",
        description="مسیر فایل لاگ"
    )
    LOG_FORMAT: str = Field(
        default="json",
        description="فرمت لاگ: json یا text"
    )
    
    # ========================================
    # Validators
    # ========================================
    
    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        """تبدیل string با کاما به لیست"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("ALLOWED_AUDIO_FORMATS", pre=True)
    def parse_audio_formats(cls, v):
        """تبدیل string با کاما به لیست"""
        if isinstance(v, str):
            return [fmt.strip().lower() for fmt in v.split(",")]
        return v
    
    @validator("ENVIRONMENT")
    def validate_environment(cls, v):
        """بررسی اعتبار محیط اجرا"""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT باید یکی از {allowed} باشد")
        return v
    
    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        """بررسی اعتبار سطح لاگ"""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed:
            raise ValueError(f"LOG_LEVEL باید یکی از {allowed} باشد")
        return v.upper()
    
    # ========================================
    # Properties
    # ========================================
    
    @property
    def is_development(self) -> bool:
        """آیا محیط development است؟"""
        return self.ENVIRONMENT == "development"
    
    @property
    def is_production(self) -> bool:
        """آیا محیط production است؟"""
        return self.ENVIRONMENT == "production"
    
    @property
    def database_url_str(self) -> str:
        """تبدیل DATABASE_URL به string"""
        return str(self.DATABASE_URL)
    
    # ========================================
    # Config
    # ========================================
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"  # نادیده گرفتن متغیرهای اضافی
    )


@lru_cache()
def get_settings() -> Settings:
    """
    دریافت تنظیمات اپلیکیشن (با cache)
    
    استفاده از lru_cache برای جلوگیری از خواندن مکرر فایل .env
    
    Returns:
        Settings: شیء تنظیمات
        
    Example:
        >>> settings = get_settings()
        >>> print(settings.APP_NAME)
    """
    return Settings()


# ========================================
# Export
# ========================================
settings = get_settings()

# Export شده برای استفاده در سایر ماژول‌ها
__all__ = ["Settings", "settings", "get_settings"]
