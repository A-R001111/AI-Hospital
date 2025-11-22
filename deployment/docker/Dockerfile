# =====================================
# مرحله 1: Base Image
# استفاده از Python 3.11 slim برای کاهش حجم
# =====================================
FROM python:3.11-slim as base

# تنظیم متغیرهای محیطی برای Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=1.6.1

# نصب پکیج‌های سیستمی مورد نیاز
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    ffmpeg \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ایجاد کاربر غیر root برای امنیت بیشتر
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app /app/logs /app/uploads && \
    chown -R appuser:appuser /app

# تنظیم دایرکتوری کاری
WORKDIR /app

# =====================================
# مرحله 2: Dependencies
# نصب وابستگی‌های Python
# =====================================
FROM base as dependencies

# کپی فایل requirements
COPY --chown=appuser:appuser backend/requirements.txt .

# ارتقا pip و نصب وابستگی‌ها
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# =====================================
# مرحله 3: Application
# کپی کد اپلیکیشن
# =====================================
FROM dependencies as application

# کپی کل پروژه
COPY --chown=appuser:appuser backend/ .
COPY --chown=appuser:appuser frontend/ ./frontend/

# تغییر مالکیت فایل‌ها به appuser
RUN chown -R appuser:appuser /app

# تغییر به کاربر appuser
USER appuser

# تنظیم PYTHONPATH
ENV PYTHONPATH=/app

# Health check برای Docker
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# =====================================
# مرحله 4: Production
# آماده‌سازی برای پروداکشن
# =====================================
FROM application as production

# Expose port
EXPOSE 8000

# دستور اجرای اپلیکیشن با Gunicorn
# استفاده از Gunicorn با Uvicorn workers برای عملکرد بهتر
CMD ["gunicorn", "app.main:app", \
    "--workers", "4", \
    "--worker-class", "uvicorn.workers.UvicornWorker", \
    "--bind", "0.0.0.0:8000", \
    "--access-logfile", "-", \
    "--error-logfile", "-", \
    "--log-level", "info", \
    "--timeout", "120", \
    "--keep-alive", "5"]

# =====================================
# مرحله 5: Development (اختیاری)
# برای محیط توسعه
# =====================================
FROM application as development

# نصب ابزارهای development
RUN pip install pytest pytest-asyncio pytest-cov black flake8 mypy isort

# Override CMD برای development
CMD ["uvicorn", "app.main:app", \
    "--host", "0.0.0.0", \
    "--port", "8000", \
    "--reload", \
    "--log-level", "debug"]
