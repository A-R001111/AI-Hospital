"""
================================================================================
Main FastAPI Application
================================================================================
فایل اصلی اپلیکیشن که تمام بخش‌ها را به هم متصل می‌کند.

شامل:
- Initialize FastAPI app
- Middleware setup (CORS, logging, rate limiting)
- Router registration
- Startup/shutdown events
- Exception handlers
================================================================================
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
import time
import logging

from app.core.config import settings
from app.core.database import init_db, check_db_connection, engine


# ========================================
# لاگ Setup
# ========================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ========================================
# Lifespan Events
# ========================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    مدیریت startup و shutdown events
    
    Startup:
    - بررسی اتصال دیتابیس
    - ایجاد جداول (در development)
    - لاگ اطلاعات اولیه
    
    Shutdown:
    - بستن اتصالات
    - cleanup منابع
    """
    # ========================================
    # Startup
    # ========================================
    logger.info("🚀 شروع راه‌اندازی اپلیکیشن...")
    
    # بررسی اتصال دیتابیس
    logger.info("🔌 بررسی اتصال دیتابیس...")
    db_healthy = await check_db_connection()
    
    if db_healthy:
        logger.info("✅ اتصال دیتابیس برقرار است")
    else:
        logger.error("❌ خطا در اتصال به دیتابیس!")
    
    # در محیط development، جداول را ایجاد کن
    if settings.is_development:
        logger.info("🔨 ایجاد جداول دیتابیس...")
        try:
            await init_db()
            logger.info("✅ جداول با موفقیت ایجاد شدند")
        except Exception as e:
            logger.error(f"❌ خطا در ایجاد جداول: {e}")
    
    # لاگ تنظیمات
    logger.info(f"📝 نام اپلیکیشن: {settings.APP_NAME}")
    logger.info(f"📝 نسخه: {settings.APP_VERSION}")
    logger.info(f"📝 محیط: {settings.ENVIRONMENT}")
    logger.info(f"📝 Debug: {settings.DEBUG}")
    logger.info(f"📝 پورت: {settings.PORT}")
    
    logger.info("✅ اپلیکیشن آماده است!")
    
    yield
    
    # ========================================
    # Shutdown
    # ========================================
    logger.info("🛑 در حال خاموش شدن...")
    
    # بستن engine دیتابیس
    await engine.dispose()
    logger.info("✅ اتصالات دیتابیس بسته شدند")
    
    logger.info("👋 خداحافظ!")


# ========================================
# FastAPI App Instance
# ========================================
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="سامانه گزارش‌نویسی پرستاران با هوش مصنوعی",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    openapi_url="/openapi.json" if settings.is_development else None,
    lifespan=lifespan
)


# ========================================
# Middleware - CORS
# ========================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)
logger.info("✅ CORS Middleware فعال شد")


# ========================================
# Middleware - GZip Compression
# ========================================
app.add_middleware(GZipMiddleware, minimum_size=1000)
logger.info("✅ GZip Middleware فعال شد")


# ========================================
# Middleware - Request Timing
# ========================================
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
    اضافه کردن زمان پردازش به header
    برای monitoring و debugging
    """
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # لاگ درخواست‌ها
    logger.info(
        f"{request.method} {request.url.path} - "
        f"{response.status_code} - {process_time:.2f}s"
    )
    
    return response


# ========================================
# Exception Handlers
# ========================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    مدیریت خطاهای validation
    """
    errors = []
    for error in exc.errors():
        errors.append({
            "field": " -> ".join(str(x) for x in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "خطا در اعتبارسنجی داده‌ها",
            "errors": errors
        }
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """
    مدیریت خطاهای دیتابیس
    """
    logger.error(f"Database error: {str(exc)}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "خطا در پردازش درخواست دیتابیس"
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    مدیریت خطاهای عمومی
    """
    logger.error(f"Unexpected error: {str(exc)}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "خطای غیرمنتظره در سرور"
        }
    )


# ========================================
# Root Endpoints
# ========================================

@app.get("/", tags=["Root"])
async def root():
    """
    Endpoint اصلی - اطلاعات کلی API
    """
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint
    
    بررسی:
    - وضعیت کلی اپلیکیشن
    - اتصال دیتابیس
    """
    db_status = await check_db_connection()
    
    return {
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }


# ========================================
# Router Registration
# ========================================
from app.api.v1 import api_router

app.include_router(api_router, prefix="/api")

logger.info("✅ API Routers registered")


# ========================================
# Static Files (Frontend)
# ========================================
import os
from pathlib import Path

# مسیر فایل‌های frontend
frontend_path = Path(__file__).parent.parent.parent / "frontend" / "templates"

if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="static")
    logger.info(f"✅ Static files mounted from {frontend_path}")
else:
    logger.warning(f"⚠️ Frontend directory not found: {frontend_path}")


# ========================================
# Development Only
# ========================================
if settings.is_development:
    @app.get("/debug/settings", tags=["Debug"])
    async def debug_settings():
        """
        نمایش تنظیمات (فقط در development)
        """
        return {
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG,
            "database_url": "***HIDDEN***",  # برای امنیت
            "cors_origins": settings.CORS_ORIGINS,
            "max_upload_size": settings.MAX_UPLOAD_SIZE,
            "allowed_audio_formats": settings.ALLOWED_AUDIO_FORMATS
        }


# ========================================
# Run Application
# ========================================
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info"
    )
