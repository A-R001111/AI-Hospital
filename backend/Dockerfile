# =====================================
# Dockerfile for Parspack PaaS
# =====================================
# =====================================
# Dockerfile برای پارس‌پک PaaS
# =====================================

FROM python:3.11-slim

# Environment Variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    ffmpeg \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for caching)
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

<<<<<<< HEAD
# Copy backend code
COPY backend/app ./app
=======
# کپی کد اپلیکیشن
COPY ./app ./app

# کپی alembic اگر وجود داشت (اختیاری)
COPY ./alembic ./alembic 2>/dev/null || echo "Alembic not found, skipping..."
>>>>>>> 682c136af2e9b7049333c32521815ca18eaa1f1a

# Copy frontend (optional)
COPY frontend ./frontend

# Create directories
RUN mkdir -p /app/logs /app/uploads && \
    chmod -R 755 /app/logs /app/uploads

# Set PYTHONPATH
ENV PYTHONPATH=/app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

<<<<<<< HEAD
# Run application
=======
# دستور اجرا
>>>>>>> 682c136af2e9b7049333c32521815ca18eaa1f1a
CMD ["gunicorn", "app.main:app", \
    "--workers", "4", \
    "--worker-class", "uvicorn.workers.UvicornWorker", \
    "--bind", "0.0.0.0:8000", \
    "--access-logfile", "-", \
    "--error-logfile", "-", \
    "--log-level", "info", \
    "--timeout", "120", \
    "--keep-alive", "5"]