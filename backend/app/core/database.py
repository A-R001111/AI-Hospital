"""
================================================================================
ماژول مدیریت دیتابیس
================================================================================
این ماژول مسئول ایجاد اتصال به دیتابیس، session management، و
تنظیمات SQLAlchemy است.

استفاده از:
- SQLAlchemy 2.0 با Async Support
- Connection Pooling برای Performance
- Session Management برای Transaction Control
================================================================================
"""

from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
    AsyncEngine
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool, QueuePool
from sqlalchemy import event, text

from app.core.config import settings


# ========================================
# تنظیمات Engine
# ========================================

def get_database_url() -> str:
    """
    تبدیل DATABASE_URL از postgresql:// به postgresql+asyncpg://
    
    asyncpg درایور async برای PostgreSQL است که با SQLAlchemy کار می‌کند.
    
    Returns:
        str: آدرس دیتابیس با درایور asyncpg
    """
    db_url = settings.database_url_str
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return db_url


def create_engine() -> AsyncEngine:
    """
    ایجاد Async Engine با مدیریت صحیح Pool
    """

    # انتخاب pool صحیح
    poolclass = QueuePool if settings.is_production else NullPool

    # پارامترهای Engine در یک dict نگه می‌داریم
    engine_params = {
        "echo": settings.DATABASE_ECHO,
        "future": True,
        "poolclass": poolclass,
        "pool_pre_ping": True,
        "pool_recycle": 3600,
        "pool_timeout": 30,
    }

    # اگر از QueuePool استفاده شود، این مقادیر مجاز هستند
    if poolclass is QueuePool:
        engine_params.update({
            "pool_size": settings.DATABASE_POOL_SIZE,
            "max_overflow": settings.DATABASE_MAX_OVERFLOW
        })

    # ساخت engine
    engine = create_async_engine(
        get_database_url(),
        **engine_params
    )

    return engine



# ========================================
# ایجاد Engine و SessionMaker
# ========================================

# Engine اصلی اپلیکیشن
engine = create_engine()

# SessionMaker برای ایجاد session های جدید
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # جلوگیری از expire شدن objects بعد از commit
    autocommit=False,  # manual control روی transaction
    autoflush=False,  # manual control روی flush
)

# Base class برای مدل‌های ORM

class Base(DeclarativeBase):
    """Base class جدید برای مدل‌ها"""
    pass


# ========================================
# Session Management
# ========================================

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    مدیریت session: باز کردن، yield، commit، rollback، بستن خودکار
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except:
            await session.rollback()
            raise



# ========================================
# توابع Helper
# ========================================

async def init_db() -> None:
    """
    ایجاد تمام جداول دیتابیس
    
    این تابع معمولاً فقط یکبار در startup اپلیکیشن اجرا می‌شود.
    در production از Alembic migrations استفاده می‌کنیم.
    
    Example:
        >>> await init_db()
    """
    async with engine.begin() as conn:
        # ایجاد تمام جداول تعریف شده در مدل‌ها
        await conn.run_sync(Base.metadata.create_all)


async def drop_db() -> None:
    """
    حذف تمام جداول دیتابیس
    
    ⚠️ خطرناک! فقط در development و testing استفاده شود!
    
    Example:
        >>> await drop_db()
    """
    if not settings.is_development:
        raise RuntimeError("drop_db فقط در محیط development مجاز است!")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def check_db_connection() -> bool:
    """
    بررسی سلامت اتصال به دیتابیس
    
    برای health check endpoint استفاده می‌شود.
    
    Returns:
        bool: True اگر اتصال سالم باشد
        
    Example:
        >>> is_healthy = await check_db_connection()
        >>> print(f"Database is {'healthy' if is_healthy else 'down'}")
    """
    try:
        async with engine.connect() as conn:
            # اجرای یک query ساده برای بررسی اتصال
            await conn.execute(text("SELECT 1"))
            return True
    except Exception as e:
        # لاگ کردن خطا
        print(f"Database health check failed: {e}")
        return False


async def get_db_version() -> Optional[str]:
    """
    دریافت نسخه PostgreSQL
    
    برای لاگ و monitoring استفاده می‌شود.
    
    Returns:
        Optional[str]: نسخه PostgreSQL یا None در صورت خطا
        
    Example:
        >>> version = await get_db_version()
        >>> print(f"PostgreSQL version: {version}")
    """
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version()"))
            row = result.fetchone()
            return row[0] if row else None
    except Exception as e:
        print(f"Failed to get database version: {e}")
        return None


# ========================================
# Event Listeners
# ========================================

# @event.listens_for(engine.sync_engine, "connect")
# def set_sqlite_pragma(dbapi_conn, connection_record):
#     """
#     تنظیمات اضافی در زمان اتصال
    
#     این event listener در زمان ایجاد هر connection اجرا می‌شود.
#     """
#     # تنظیمات خاص PostgreSQL می‌تواند اینجا اضافه شود
#     pass

@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """
    اجرای PRAGMA فقط برای SQLite، نه PostgreSQL
    """
    if "sqlite" not in str(engine.url):
        return  # اگر SQLite نبود، هیچی اجرا نشود

    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.execute("PRAGMA busy_timeout=30000;")
    cursor.close()


@event.listens_for(engine.sync_engine, "close")
def receive_close(dbapi_conn, connection_record):
    """
    لاگ کردن بستن connection
    
    برای monitoring و debugging استفاده می‌شود.
    """
    # می‌توان اینجا لاگ گذاشت
    pass


# ========================================
# Context Manager برای Manual Session
# ========================================

class DatabaseSession:
    """
    Context Manager برای استفاده دستی از session
    
    زمانی استفاده می‌شود که خارج از endpoint نیاز به session داریم.
    
    Example:
        >>> async with DatabaseSession() as session:
        >>>     result = await session.execute(select(User))
        >>>     users = result.scalars().all()
    """
    
    def __init__(self):
        self.session: Optional[AsyncSession] = None
    
    async def __aenter__(self) -> AsyncSession:
        """ورود به context"""
        self.session = AsyncSessionLocal()
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """خروج از context"""
        if exc_type is not None:
            # در صورت خطا، rollback
            await self.session.rollback()
        else:
            # در غیر این صورت، commit
            await self.session.commit()
        
        # بستن session
        await self.session.close()


# ========================================
# Export
# ========================================
__all__ = [
    "engine",
    "AsyncSessionLocal",
    "Base",
    "get_db",
    "init_db",
    "drop_db",
    "check_db_connection",
    "get_db_version",
    "DatabaseSession",
]
