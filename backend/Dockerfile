# =====================================
# Dockerfile برای پارس‌پک PaaS
# این فایل باید در: backend/Dockerfile
# =====================================
# =====================================
# Dockerfile برای پارس‌پک PaaS
# =====================================

FROM python:3.11-slim

# متغیرهای محیطی Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# نصب dependencies سیستمی
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    ffmpeg \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# تنظیم working directory
WORKDIR /app

# کپی requirements و نصب
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# کپی کد اپلیکیشن
COPY ./app ./app

# کپی alembic اگر وجود داشت (اختیاری)
COPY ./alembic ./alembic 2>/dev/null || echo "Alembic not found, skipping..."

# ایجاد دایرکتوری‌های مورد نیاز
RUN mkdir -p /app/logs /app/uploads && \
    chmod -R 755 /app/logs /app/uploads

# تنظیم PYTHONPATH
ENV PYTHONPATH=/app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# دستور اجرا
CMD ["gunicorn", "app.main:app", \
    "--workers", "4", \
    "--worker-class", "uvicorn.workers.UvicornWorker", \
    "--bind", "0.0.0.0:8000", \
    "--access-logfile", "-", \
    "--error-logfile", "-", \
    "--log-level", "info", \
    "--timeout", "120", \
    "--keep-alive", "5"]
