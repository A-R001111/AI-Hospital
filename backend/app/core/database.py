# # ================================================================================
# # ماژول مدیریت دیتابیس
# # ================================================================================
# # این فایل مسئول:
# # - ساخت Engine با asyncpg
# # - مدیریت Session ها
# # - ایجاد و حذف جداول
# # - توابع کمکی برای Health Check
# # ================================================================================

# from typing import AsyncGenerator, Optional

# from sqlalchemy.ext.asyncio import (
#     AsyncSession,
#     create_async_engine,
#     async_sessionmaker,
#     AsyncEngine
# )

# from sqlalchemy.orm import DeclarativeBase
# from sqlalchemy import text
# from sqlalchemy.pool import NullPool

# from app.core.config import settings


# # ================================================================================
# # کلاس Base برای ORM
# # ================================================================================
# class Base(DeclarativeBase):
#     """تمام مدل‌های دیتابیس باید از این Base ارث‌بری کنند"""
#     pass


# # ================================================================================
# # تبدیل URL دیتابیس برای asyncpg
# # ================================================================================
# def get_database_url() -> str:
#     """
#     تبدیل postgresql:// به postgresql+asyncpg:// برای سازگاری کامل
#     """
#     url = settings.database_url_str
#     if url.startswith("postgresql://"):
#         url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
#     return url


# # ================================================================================
# # ساخت Engine اصلی برنامه
# # ================================================================================
# def create_engine() -> AsyncEngine:
#     """
#     ساخت Engine با NullPool چون asyncpg خودش مدیریت اتصال را انجام می‌دهد.
#     """
#     return create_async_engine(
#         get_database_url(),
#         echo=settings.DATABASE_ECHO,
#         future=True,
#         poolclass=NullPool
#     )


# # Engine نهایی
# engine = create_engine()


# # ================================================================================
# # Session Factory برای کنترل تراکنش‌ها
# # ================================================================================
# AsyncSessionLocal = async_sessionmaker(
#     engine,
#     class_=AsyncSession,
#     expire_on_commit=False,   # جلوگیری از پاک شدن داده بعد از commit
#     autocommit=False,         # کنترل دستی commit
#     autoflush=False           # کنترل دستی flush
# )


# # ================================================================================
# # Dependency FastAPI برای مدیریت Session
# # ================================================================================
# async def get_db() -> AsyncGenerator[AsyncSession, None]:
#     """
#     مدیریت خودکار:
#     - ساخت session
#     - yield به endpoint
#     - commit در حالت موفق
#     - rollback در حالت خطا
#     - بستن ارتباط
#     """
#     async with AsyncSessionLocal() as session:
#         try:
#             yield session
#             await session.commit()
#         except:
#             await session.rollback()
#             raise


# # ================================================================================
# # ایجاد جداول دیتابیس
# # ================================================================================
# async def init_db() -> None:
#     """
#     ایجاد جداول بر اساس تمام مدل‌هایی که از Base ارث‌بری کرده‌اند.
#     """
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)


# # ================================================================================
# # حذف تمام جداول (فقط مخصوص توسعه)
# # ================================================================================
# async def drop_db() -> None:
#     """
#     حذف تمام جداول.
#     استفاده در Production کاملاً غیرمجاز است.
#     """
#     if not settings.is_development:
#         raise RuntimeError("drop_db فقط در حالت توسعه مجاز است.")

#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.drop_all)


# # ================================================================================
# # بررسی سلامت دیتابیس
# # ================================================================================
# async def check_db_connection() -> bool:
#     """
#     اجرای یک query ساده برای مطمئن شدن از فعال بودن اتصال دیتابیس.
#     """
#     try:
#         async with engine.connect() as conn:
#             await conn.execute(text("SELECT 1"))
#         return True
#     except Exception as e:
#         print("DB connection error:", e)
#         return False


# # ================================================================================
# # دریافت نسخه دیتابیس PostgreSQL
# # ================================================================================
# async def get_db_version() -> Optional[str]:
#     try:
#         async with engine.connect() as conn:
#             result = await conn.execute(text("SELECT version()"))
#             row = result.fetchone()
#             return row[0] if row else None
#     except:
#         return None


# # ================================================================================
# # Context Manager برای استفاده دستی از Session
# # ================================================================================
# class DatabaseSession:
#     """
#     زمانی استفاده می‌شود که خارج از endpoint نیاز به session داشته باشیم.
#     """
#     def __init__(self):
#         self.session: Optional[AsyncSession] = None

#     async def __aenter__(self) -> AsyncSession:
#         self.session = AsyncSessionLocal()
#         return self.session

#     async def __aexit__(self, exc_type, exc_val, exc_tb):
#         if exc_type:
#             await self.session.rollback()
#         else:
#             await self.session.commit()
#         await self.session.close()


# # ================================================================================
# # خروجی‌ها
# # ================================================================================
# __all__ = [
#     "engine",
#     "AsyncSessionLocal",
#     "Base",
#     "get_db",
#     "init_db",
#     "drop_db",
#     "check_db_connection",
#     "get_db_version",
#     "DatabaseSession"
# ]

# app/core/database.py
# ========================================
# مدیریت اتصال به دیتابیس (SQLAlchemy async)
# ========================================

from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
    AsyncEngine
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from sqlalchemy.pool import NullPool, QueuePool
from app.core.config import settings

# تبدیل DATABASE_URL استاندارد (postgresql://) به ورژن async (postgresql+asyncpg://)
def get_database_url() -> str:
    url = settings.database_url_str
    if url.startswith("postgresql://"):
        # اگر کاربر رشته اتصال را به صورت معمولی (بدون +asyncpg) وارد کرده است،
        # اینجا آن را به فرمتی که asyncpg می‌فهمد تبدیل می‌کنیم.
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url

def create_engine() -> AsyncEngine:
    """
    ایجاد engine سازگار با SQLAlchemy async.
    در محیط development از NullPool استفاده می‌کنیم (بدون pool) تا مشکلات محلی کاهش یابد.
    در محیط production اگر خواستی QueuePool فعال می‌شود و پارامترهای pool اضافه می‌شوند.
    """
    # اگر در production هستیم، از QueuePool استفاده کن تا اتصال‌ها در pool نگه داشته شوند
    if settings.is_production:
        # اینجا پارامترهای pool را تنها زمانی اضافه می‌کنیم که QueuePool استفاده شود
        engine = create_async_engine(
            get_database_url(),
            echo=settings.DATABASE_ECHO,
            future=True,
            poolclass=QueuePool,
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
            pool_recycle=3600,
        )
    else:
        # در development از NullPool (بدون پارامترهایی که با NullPool ناسازگارند) استفاده می‌کنیم
        engine = create_async_engine(
            get_database_url(),
            echo=settings.DATABASE_ECHO,
            future=True,
            poolclass=NullPool,
        )

    return engine

# ========================================
# ایجاد engine و session factory
# ========================================
engine = create_engine()

class Base(DeclarativeBase):
    """Base class جدید برای مدل‌ها (SQLAlchemy 2.0 style)"""
    pass

# factory ساخت session های async
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # جلوگیری از منقضی شدن اشیاء بعد از commit
    autoflush=False,
    autocommit=False,
)

# Dependency برای FastAPI: فراهم کردن یک session برای هر request
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    # باز کردن session
    async with AsyncSessionLocal() as session:
        try:
            # yield کردن session تا endpoint از آن استفاده کند
            yield session
            # commit اگر endpoint بدون استثناء خاتمه یافت
            await session.commit()
        except:
            # اگر استثناء رخ داد rollback شود
            await session.rollback()
            raise

# توابع کمکی
async def init_db() -> None:
    """ایجاد جداول (فقط برای development; در production از migrations استفاده کن)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def drop_db() -> None:
    """حذف جداول (فقط در development)"""
    if not settings.is_development:
        raise RuntimeError("drop_db فقط برای محیط development مجاز است")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

async def check_db_connection() -> bool:
    """اجرای SELECT 1 برای بررسی سلامت اتصال"""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"DB connection error: {e}")
        return False

# Context manager دستی (در صورتی که خارج از DI خواستی session داشته باشی)
class DatabaseSession:
    def __init__(self):
        self.session: Optional[AsyncSession] = None

    async def __aenter__(self) -> AsyncSession:
        self.session = AsyncSessionLocal()
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.session.rollback()
        else:
            await self.session.commit()
        await self.session.close()

__all__ = [
    "engine",
    "AsyncSessionLocal",
    "Base",
    "get_db",
    "init_db",
    "drop_db",
    "check_db_connection",
    "DatabaseSession",
]

