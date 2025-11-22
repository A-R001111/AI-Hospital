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
from sqlalchemy.orm import declarative_base
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
    ایجاد Async Engine برای SQLAlchemy
    
    تنظیمات:
    - Connection Pooling برای بهینه‌سازی performance
    - Echo برای نمایش SQL queries در development
    - Pool Pre-ping برای بررسی سلامت connection
    
    Returns:
        AsyncEngine: موتور async دیتابیس
    """
    # انتخاب نوع Pool بر اساس محیط
    if settings.is_production:
        poolclass = QueuePool
        pool_pre_ping = True
    else:
        # در development از NullPool استفاده می‌کنیم برای debugging آسان‌تر
        poolclass = NullPool if settings.DEBUG else QueuePool
        pool_pre_ping = False
    
    engine = create_async_engine(
        get_database_url(),
        echo=settings.DATABASE_ECHO,  # نمایش SQL queries
        future=True,  # استفاده از API جدید SQLAlchemy 2.0
        pool_size=settings.DATABASE_POOL_SIZE,  # تعداد connection های ثابت در pool
        max_overflow=settings.DATABASE_MAX_OVERFLOW,  # حداکثر connection اضافی
        pool_pre_ping=pool_pre_ping,  # بررسی سلامت connection قبل از استفاده
        poolclass=poolclass,
        pool_recycle=3600,  # بازسازی connection ها بعد از 1 ساعت
        pool_timeout=30,  # timeout برای گرفتن connection از pool
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
Base = declarative_base()


# ========================================
# Session Management
# ========================================

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency برای دریافت database session در endpoint ها
    
    این تابع یک async context manager است که session را ایجاد کرده،
    در اختیار endpoint قرار می‌دهد، و در نهایت آن را close می‌کند.
    
    در صورت بروز خطا، transaction به صورت خودکار rollback می‌شود.
    
    Yields:
        AsyncSession: نشست دیتابیس
        
    Example در endpoint:
        >>> @app.get("/users")
        >>> async def get_users(db: AsyncSession = Depends(get_db)):
        >>>     result = await db.execute(select(User))
        >>>     return result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            # ارائه session به endpoint
            yield session
            
            # اگر تا اینجا خطایی نبود، commit می‌کنیم
            await session.commit()
            
        except Exception:
            # در صورت خطا، rollback می‌کنیم
            await session.rollback()
            raise
            
        finally:
            # در هر صورت session را close می‌کنیم
            await session.close()


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

@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """
    تنظیمات اضافی در زمان اتصال
    
    این event listener در زمان ایجاد هر connection اجرا می‌شود.
    """
    # تنظیمات خاص PostgreSQL می‌تواند اینجا اضافه شود
    pass


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
