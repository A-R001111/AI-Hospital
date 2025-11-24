# =====================================
# Dockerfile for Parspack PaaS
# نسخه اصلاح‌شده — شامل نصب اختیاری PyTorch (CPU) و بهبود امنیت و caching
# =====================================

# پایه تصویر پایتون 3.11 slim
FROM python:3.11-slim

# تنظیم متغیرهای محیطی پایتون برای رفتار مطلوب در کانتینر
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

# آرگومان برای فعال/غیرفعال کردن نصب Torch در زمان build
# هنگام build می‌توان از --build-arg INSTALL_TORCH=true استفاده کرد.
ARG INSTALL_TORCH=false

# =====================================
# نصب بسته‌های سیستمی مورد نیاز
# توضیح: libgomp1 برای پردازش‌های عددی (مثلاً OpenBLAS) لازم است
# و جلوی خطاهای runtime را می‌گیرد.
# همه بسته‌ها در یک RUN برای کاهش تعداد لایه‌ها
# و پاکسازی کش apt برای کوچک‌تر شدن image
# =====================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    libpq-dev \
    ffmpeg \
    libmagic1 \
    curl \
    libgomp1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# =====================================
# ست کردن مسیر کاری
# =====================================
WORKDIR /app

# =====================================
# کپی فایل requirements واقعی
# این فایل باید فقط شامل پکیج‌های پایتون باشد.
# کپی قبل از کد برای استفاده از Docker layer caching
# =====================================
COPY backend/requirements.txt ./backend/requirements.txt

# ارتقا pip، setuptools و wheel
RUN python -m pip install --upgrade pip setuptools wheel

# =====================================
# نصب اختیاری PyTorch و torchaudio (CPU)
# این مرحله تنها زمانی اجرا می‌شود که آرگومان INSTALL_TORCH=true باشد
# =====================================
RUN if [ "${INSTALL_TORCH}" = "true" ]; then \
      python -m pip install --no-cache-dir "torch==2.1.1+cpu" "torchaudio==2.1.1+cpu" -f https://download.pytorch.org/whl/torch_stable.html ; \
    else \
      echo "Skipping torch install (INSTALL_TORCH not true)"; \
    fi

# =====================================
# نصب باقی پکیج‌های requirements بدون حل مجدد وابستگی‌ها
# (--no-deps) جلوگیری می‌کند از بازنویسی نسخه‌های نصب شده
# =====================================
RUN python -m pip install --no-cache-dir --no-deps -r ./backend/requirements.txt

# =====================================
# کپی کدهای backend
# =====================================
COPY backend/app ./app

# کپی frontend (در صورت وجود)
COPY frontend ./frontend

# =====================================
# ایجاد فولدرهای runtime و تنظیم دسترسی مناسب
# =====================================
RUN mkdir -p /app/logs /app/uploads && chmod -R 755 /app/logs /app/uploads

# تنظیم PYTHONPATH برای اطمینان از ایمپورت درست ماژول‌ها
ENV PYTHONPATH=/app

# =====================================
# Health check ساده — endpoint /health باید در اپ تعریف شده باشد
# =====================================
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://127.0.0.1:8000/health || exit 1

# =====================================
# پورت اپلیکیشن
# =====================================
EXPOSE 8000

# =====================================
# دستور اجرای برنامه — Gunicorn با Uvicorn worker
# تعداد worker=2 برای کاهش مصرف حافظه در محیط محدود
# =====================================
CMD ["gunicorn","app.main:app","--workers","2","--worker-class","uvicorn.workers.UvicornWorker","--bind","0.0.0.0:8000","--access-logfile","-","--error-logfile","-","--log-level","info","--timeout","120","--keep-alive","5"]
