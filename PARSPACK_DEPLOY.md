# 🚀 راهنمای استقرار روی پارس‌پک

## مرحله 1: آماده‌سازی پروژه

### 1.1 بررسی فایل‌های لازم
```bash
# مطمئن شوید این فایل‌ها وجود دارند:
ls -la deployment/docker/Dockerfile
ls -la docker-compose.yml
ls -la .env.example
```

### 1.2 ایجاد فایل .env
```bash
cp .env.example .env
# ویرایش و پر کردن مقادیر واقعی
nano .env
```

## مرحله 2: ورود به پنل پارس‌پک

1. به آدرس https://my.parspack.com بروید
2. وارد حساب کاربری خود شوید
3. از منوی سمت چپ "سرویس PaaS" را انتخاب کنید

## مرحله 3: ایجاد اپلیکیشن جدید

### 3.1 انتخاب نوع اپلیکیشن
1. روی دکمه "ایجاد اپلیکیشن" کلیک کنید
2. نوع اپلیکیشن را "Docker Application" انتخاب کنید
3. نام اپلیکیشن: `hospital-reports`

### 3.2 تنظیم Git Repository
**روش 1: استفاده از GitHub (توصیه می‌شود)**
```
Repository URL: https://github.com/YOUR-USERNAME/AI-Hospital
Branch: main
```

**روش 2: استفاده از Git Manual**
- فایل `deployment/docker/Dockerfile` را آپلود کنید
- یا از GitLab/BitBucket استفاده کنید

### 3.3 تنظیم Dockerfile
```
Dockerfile Path: deployment/docker/Dockerfile
Build Context: ./
Target: production
```

## مرحله 4: تنظیم متغیرهای محیطی

در بخش "Environment Variables" متغیرهای زیر را اضافه کنید:

```env
# Application
APP_NAME=سامانه گزارش‌نویسی
ENVIRONMENT=production
DEBUG=False

# Database (پارس‌پک PostgreSQL addon)
DATABASE_URL=postgresql://USER:PASS@postgres-host:5432/dbname

# Security
SECRET_KEY=<یک کلید 32 کاراکتری تصادفی>
ACCESS_TOKEN_EXPIRE_MINUTES=30

# OpenAI
OPENAI_API_KEY=<کلید API OpenAI شما>

# Redis (پارس‌پک Redis addon)
REDIS_HOST=redis-host
REDIS_PORT=6379
REDIS_PASSWORD=<رمز Redis>

# CORS
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### نکات مهم:
- از Secret Variables برای `SECRET_KEY` و `OPENAI_API_KEY` استفاده کنید
- `DATABASE_URL` را از addon PostgreSQL پارس‌پک دریافت کنید

## مرحله 5: افزودن Database و Cache

### 5.1 PostgreSQL Database
1. در پنل پارس‌پک به "Addons" بروید
2. "PostgreSQL" را انتخاب کنید
3. نسخه 15 را انتخاب کنید
4. به اپلیکیشن `hospital-reports` متصل کنید
5. DATABASE_URL را از اینجا کپی کنید

### 5.2 Redis Cache
1. Addon "Redis" را اضافه کنید
2. نسخه 7 را انتخاب کنید
3. REDIS_HOST و REDIS_PASSWORD را یادداشت کنید

## مرحله 6: تنظیم دامنه

### 6.1 اتصال دامنه شخصی
1. به بخش "Domains" بروید
2. دامنه خود را وارد کنید
3. رکوردهای DNS را طبق راهنمای پارس‌پک تنظیم کنید:

```
Type: A
Name: @
Value: <IP پارس‌پک>

Type: CNAME
Name: www
Value: <آدرس پارس‌پک>
```

### 6.2 فعال‌سازی SSL
1. در بخش SSL روی "Enable SSL" کلیک کنید
2. Let's Encrypt (رایگان) را انتخاب کنید
3. صبر کنید تا گواهی صادر شود

## مرحله 7: Deploy

### 7.1 اولین Deploy
1. روی دکمه "Deploy" کلیک کنید
2. منتظر بمانید تا build و deployment کامل شود
3. لاگ‌ها را بررسی کنید

### 7.2 بررسی سلامت
```bash
# بررسی health endpoint
curl https://yourdomain.com/health

# باید پاسخ "OK" دریافت کنید
```

## مرحله 8: مایگریشن دیتابیس

```bash
# اتصال به کنسول اپلیکیشن در پارس‌پک
# سپس اجرای:
alembic upgrade head
```

یا در صورت نبود alembic:
```bash
# ایجاد اولیه جداول
python -c "from app.core.database import init_db; import asyncio; asyncio.run(init_db())"
```

## مرحله 9: ایجاد کاربر ادمین اولیه

```bash
# در کنسول اپلیکیشن:
python scripts/create_admin.py
```

یا با API:
```bash
curl -X POST https://yourdomain.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "employee_code": "ADMIN001",
    "first_name": "Admin",
    "last_name": "System",
    "email": "admin@hospital.com",
    "password": "SecurePass123!",
    "role": "admin"
  }'
```

## مرحله 10: تست و Monitoring

### 10.1 تست API
```bash
# ورود
curl -X POST https://yourdomain.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@hospital.com",
    "password": "SecurePass123!"
  }'
```

### 10.2 مشاهده Logs
در پنل پارس‌پک به بخش "Logs" بروید و لاگ‌های real-time را ببینید.

### 10.3 Monitoring
- CPU Usage
- Memory Usage
- Request Count
- Response Time

## روش‌های Auto Deploy

### روش 1: Git Push (توصیه می‌شود)
```bash
# هر push به branch main به صورت خودکار deploy می‌شود
git add .
git commit -m "Update"
git push origin main
```

### روش 2: Webhook
پارس‌پک به صورت خودکار webhook GitHub را راه‌اندازی می‌کند.

## رفع مشکلات رایج

### خطای Database Connection
```bash
# بررسی DATABASE_URL
echo $DATABASE_URL

# تست اتصال
psql $DATABASE_URL -c "SELECT 1"
```

### خطای Out of Memory
- منابع پلن PaaS را افزایش دهید
- Workers در Gunicorn را کاهش دهید

### خطای SSL
```bash
# بررسی DNS
dig yourdomain.com
dig www.yourdomain.com

# صبر کنید 24 ساعت برای propagation
```

## Backup و Restore

### Backup خودکار
پارس‌پک به صورت روزانه backup می‌گیرد.

### Backup دستی
```bash
# در local:
pg_dump $DATABASE_URL > backup.sql

# آپلود به فضای ابری پارس‌پک
```

## Scale کردن

### Horizontal Scaling
در پنل پارس‌پک:
1. به بخش "Scale" بروید
2. تعداد instances را افزایش دهید

### Vertical Scaling
1. پلن PaaS را ارتقا دهید
2. منابع بیشتری اختصاص دهید

## مستندات بیشتر

- داکیومنت پارس‌پک: https://docs.parspack.com
- پشتیبانی: support@parspack.com
- تیکت: https://my.parspack.com/tickets
