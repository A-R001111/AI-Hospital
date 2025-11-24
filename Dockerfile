# =====================================
# Dockerfile for Parspack PaaS
# نسخه اصلاح‌شده — شامل نصب اختیاری PyTorch (CPU) و بهبود امنیت و caching
# =====================================

FROM python:3.11-slim

# تنظیم متغیرهای محیطی پایتون برای رفتار مطلوب در کانتینر
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# آرگومان برای فعال/غیرفعال کردن نصب Torch در زمان build
# اگر بخواهی Torch را نصب کنی هنگام build از --build-arg INSTALL_TORCH=true استفاده کن.
ARG INSTALL_TORCH=false

# نصب بسته‌های سیستمی مورد نیاز
# توضیح: libgomp1 معمولا برای پردازش‌های عددی (openblas) لازم است و جلوگیری از runtime error می‌کند.
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    ffmpeg \
    libmagic1 \
    curl \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# ست کردن مسیر کاری
WORKDIR /app

# کپی requirements قبل از کپی کد برای استفاده از layer caching Docker
COPY backend/requirements.txt ./backend/requirements.txt

# ارتقا pip با روش پیشنهادی (python -m pip) و امن‌سازی نصب پکیج‌ها
RUN python -m pip install --upgrade pip setuptools wheel

# --- نصب اختیاری PyTorch/torchaudio (CPU) از شاخص رسمی PyTorch ---
# نکته: این مرحله تنها زمانی اجرا می‌شود که هنگام build آرگومان INSTALL_TORCH=true ارسال شده باشد.
# همچنین از index رسمی PyTorch استفاده می‌کنیم تا wheel مناسب پلتفرم دانلود شود.
RUN if [ "${INSTALL_TORCH}" = "true" ]; then \
      python -m pip install --no-cache-dir "torch==2.1.1+cpu" "torchaudio==2.1.1+cpu" -f https://download.pytorch.org/whl/torch_stable.html ; \
    else \
      echo "Skipping torch install (INSTALL_TORCH not true)"; \
    fi

# نصب باقی requirements بدون حل مجدد وابستگی‌ها (--no-deps) تا از بازنویسی نسخه‌های نصب‌شده جلوگیری شود.
# توضیح: اگر torch/torchaudio را نصب کردیم، نمی‌خواهیم pip در این مرحله تلاش کند دوباره آن‌ها را حل کند.
RUN python -m pip install --no-cache-dir --no-deps -r ./backend/requirements.txt

# حالا کدهای backend را کپی می‌کنیم
COPY backend/app ./app

# کپی frontend (در صورت وجود)
COPY frontend ./frontend

# فولدرهای runtime و تنظیم دسترسی مناسب
RUN mkdir -p /app/logs /app/uploads && chmod -R 755 /app/logs /app/uploads

# تنظیم PYTHONPATH برای اطمینان از ایمپورت درست ماژول‌ها
ENV PYTHONPATH=/app

# Health check ساده — توجه کن که endpoint /health باید در اپ تعریف شده باشد.
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://127.0.0.1:8000/health || exit 1

# پورت اپلیکیشن
EXPOSE 8000

# دستور اجرای برنامه — Gunicorn با Uvicorn worker
CMD ["gunicorn", "app.main:app", \
    "--workers", "4", \
    "--worker-class", "uvicorn.workers.UvicornWorker", \
    "--bind", "0.0.0.0:8000", \
    "--access-logfile", "-", \
    "--error-logfile", "-", \
    "--log-level", "info", \
    "--timeout", "120", \
    "--keep-alive", "5"]
