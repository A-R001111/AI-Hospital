# 🏥 AI Hospital - سامانه گزارش‌نویسی هوشمند پرستاران

یک سامانه **حرفه‌ای** و **مدرن** برای ثبت و مدیریت گزارشات پرستاری با قابلیت **تبدیل صدا به متن** با هوش مصنوعی.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?logo=postgresql)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker)](https://docker.com)

---

## 📋 فهرست مطالب

- [ویژگی‌ها](#-ویژگی‌ها)
- [معماری](#-معماری)
- [پیش‌نیازها](#-پیش‌نیازها)
- [نصب و راه‌اندازی](#-نصب-و-راه‌اندازی)
- [استفاده](#-استفاده)
- [API Documentation](#-api-documentation)
- [ساختار پروژه](#-ساختار-پروژه)
- [تست](#-تست)
- [مشارکت](#-مشارکت)
- [لایسنس](#-لایسنس)

---

## 🌟 ویژگی‌ها

### ✅ Core Features

- **🎤 ضبط صدا**: ضبط مستقیم گزارشات صوتی از مرورگر
- **🤖 Speech-to-Text**: تبدیل خودکار صدا به متن با OpenAI Whisper
- **📝 ویرایشگر متن**: امکان ویرایش و بهبود گزارشات
- **👥 مدیریت کاربران**: سیستم کامل احراز هویت و مجوزها
- **📊 آمار و گزارش**: داشبورد آماری جامع
- **🔒 امنیت بالا**: JWT Authentication, bcrypt hashing

### 🎯 Technical Highlights

- **Async/Await**: عملکرد بالا با FastAPI async
- **Type Safety**: استفاده کامل از Type Hints
- **Clean Architecture**: معماری لایه‌ای و مدولار
- **Docker Ready**: آماده برای deployment
- **API First**: RESTful API با OpenAPI documentation
- **Real-time**: WebSocket support (در نسخه‌های آینده)

---

## 🏗️ معماری

### Technology Stack

#### Backend
```
FastAPI 0.109.0       # Web Framework
SQLAlchemy 2.0        # ORM (Async)
PostgreSQL 15         # Database
Redis 7               # Caching
Pydantic 2.5          # Data Validation
JWT                   # Authentication
bcrypt                # Password Hashing
OpenAI Whisper        # Speech-to-Text
```

#### Frontend
```
HTML5 + CSS3          # Structure & Style
Vanilla JavaScript    # Logic
Web Audio API         # Voice Recording
Vazirmatn Font        # Persian Typography
```

#### Infrastructure
```
Docker & Docker Compose
Nginx                 # Reverse Proxy
Let's Encrypt         # SSL/TLS
```

### Architecture Layers

```
┌─────────────────────────────────────────┐
│           Frontend (HTML/JS)             │
├─────────────────────────────────────────┤
│         API Layer (FastAPI)              │
│  ┌──────────────────────────────────┐   │
│  │  Routers (auth, reports, users)  │   │
│  └──────────────────────────────────┘   │
├─────────────────────────────────────────┤
│        Service Layer (Business)          │
│  ┌──────────────────────────────────┐   │
│  │  AuthService, ReportService      │   │
│  │  VoiceService (Whisper API)      │   │
│  └──────────────────────────────────┘   │
├─────────────────────────────────────────┤
│         Data Layer (SQLAlchemy)          │
│  ┌──────────────────────────────────┐   │
│  │  Models: User, Report            │   │
│  │  Schemas: Pydantic Validation    │   │
│  └──────────────────────────────────┘   │
├─────────────────────────────────────────┤
│     Database (PostgreSQL + Redis)        │
└─────────────────────────────────────────┘
```

---

## 🔧 پیش‌نیازها

### نصب با Docker (توصیه می‌شود)
- Docker 20.10+
- Docker Compose 2.0+

### نصب Manual
- Python 3.11+
- PostgreSQL 15+
- Redis 7+ (اختیاری)
- Node.js 18+ (برای development frontend)

---

## 🚀 نصب و راه‌اندازی

### روش 1: Quick Start با Docker (⚡ سریع)

```bash
# 1. Clone repository
git clone https://github.com/your-username/AI-Hospital.git
cd AI-Hospital

# 2. تنظیم Environment Variables
cp .env.example .env
# ویرایش .env و پر کردن مقادیر

# 3. اجرا با یک دستور!
./quick-start.sh

# یا به صورت manual:
docker-compose up -d
```

**✅ Done!** سیستم در `http://localhost:8000` آماده است.

### روش 2: نصب Manual (برای Development)

#### 1. نصب وابستگی‌های Python

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### 2. راه‌اندازی PostgreSQL

```bash
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql

# macOS
brew install postgresql@15
brew services start postgresql@15

# Windows
# دانلود از postgresql.org
```

#### 3. ایجاد دیتابیس

```bash
createuser -s hospital_user
createdb -O hospital_user hospital_db
```

#### 4. تنظیم Environment Variables

```bash
cp .env.example .env
nano .env
```

**حداقل تنظیمات لازم:**
```env
# Database
DATABASE_URL=postgresql+asyncpg://hospital_user:password@localhost/hospital_db

# Security
SECRET_KEY=your-super-secret-key-min-32-characters-long!!
ALGORITHM=HS256

# OpenAI (برای Voice-to-Text)
OPENAI_API_KEY=sk-your-openai-api-key-here

# App
APP_NAME=AI Hospital
ENVIRONMENT=development
DEBUG=True
```

#### 5. اجرای Migrations

```bash
# در مرحله development، جداول خودکار ساخته می‌شوند
# برای production:
alembic upgrade head
```

#### 6. اجرای Backend

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 7. دسترسی به Frontend

```
http://localhost:8000/login.html
```

---

## 💻 استفاده

### 1. ثبت‌نام و ورود

#### ثبت‌نام کاربر جدید
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "employee_code": "NUR001",
    "first_name": "فاطمه",
    "last_name": "احمدی",
    "email": "nurse@hospital.com",
    "password": "SecurePass123!",
    "role": "nurse",
    "department": "ICU"
  }'
```

#### ورود به سیستم
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "nurse@hospital.com",
    "password": "SecurePass123!"
  }'
```

**پاسخ:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "uuid-here",
    "email": "nurse@hospital.com",
    "first_name": "فاطمه",
    "role": "nurse"
  }
}
```

### 2. ایجاد گزارش متنی

```bash
curl -X POST "http://localhost:8000/api/v1/reports" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_name": "علی محمدی",
    "patient_file_number": "P-2024-001",
    "patient_national_id": "1234567890",
    "content": "بیمار در وضعیت پایدار قرار دارد. علائم حیاتی در محدوده طبیعی. درمان طبق برنامه ادامه دارد.",
    "notes": "کنترل مجدد در شیفت بعدی"
  }'
```

### 3. ایجاد گزارش صوتی

```bash
curl -X POST "http://localhost:8000/api/v1/reports/voice" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "audio_file=@recording.wav" \
  -F "patient_name=علی محمدی" \
  -F "patient_file_number=P-2024-001"
```

### 4. دریافت لیست گزارشات

```bash
curl -X GET "http://localhost:8000/api/v1/reports?page=1&page_size=10" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 5. آمار گزارشات

```bash
curl -X GET "http://localhost:8000/api/v1/reports/stats/summary" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## 📚 API Documentation

### Interactive API Docs

بعد از راه‌اندازی، به آدرس‌های زیر بروید:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Main Endpoints

#### Authentication
```
POST   /api/v1/auth/register      # ثبت‌نام
POST   /api/v1/auth/login         # ورود
POST   /api/v1/auth/refresh       # تمدید token
GET    /api/v1/auth/me            # اطلاعات کاربر
POST   /api/v1/auth/logout        # خروج
```

#### Reports
```
POST   /api/v1/reports            # ایجاد گزارش متنی
POST   /api/v1/reports/voice      # ایجاد گزارش صوتی
GET    /api/v1/reports            # لیست گزارشات
GET    /api/v1/reports/{id}       # دریافت یک گزارش
PUT    /api/v1/reports/{id}       # ویرایش گزارش
DELETE /api/v1/reports/{id}       # حذف گزارش
GET    /api/v1/reports/stats/summary  # آمار
```

---

## 📁 ساختار پروژه

```
AI-Hospital/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI application
│   │   ├── core/
│   │   │   ├── config.py              # تنظیمات
│   │   │   ├── security.py            # JWT, bcrypt
│   │   │   └── database.py            # SQLAlchemy setup
│   │   ├── models/
│   │   │   ├── user.py                # User model
│   │   │   └── report.py              # Report model
│   │   ├── schemas/
│   │   │   ├── user.py                # Pydantic schemas
│   │   │   └── report.py              # Pydantic schemas
│   │   ├── services/
│   │   │   ├── auth_service.py        # Business logic
│   │   │   ├── report_service.py      # Business logic
│   │   │   └── voice_service.py       # Whisper integration
│   │   └── api/
│   │       ├── dependencies.py        # Dependency injection
│   │       └── v1/
│   │           ├── auth.py            # Auth endpoints
│   │           └── reports.py         # Report endpoints
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   └── templates/
│       ├── login.html                 # صفحه ورود
│       └── dashboard.html             # داشبورد
├── deployment/
│   ├── docker/
│   │   └── Dockerfile
│   └── nginx/
│       └── nginx.conf
├── docker-compose.yml
├── .env.example
├── quick-start.sh
└── README.md
```

---

## 🧪 تست

### اجرای Unit Tests

```bash
cd backend
pytest tests/ -v
```

### اجرای Tests با Coverage

```bash
pytest tests/ --cov=app --cov-report=html
```

### اجرای Integration Tests

```bash
pytest tests/integration/ -v
```

---

## 🔐 امنیت

### Best Practices

- ✅ JWT Authentication با refresh token
- ✅ Password hashing با bcrypt (cost factor 12)
- ✅ CORS configuration صحیح
- ✅ Rate limiting (در production)
- ✅ SQL Injection prevention (SQLAlchemy ORM)
- ✅ XSS prevention
- ✅ HTTPS only (در production)

### Environment Variables

**⚠️ هرگز فایل `.env` را commit نکنید!**

همیشه `.env.example` را به‌روز نگه دارید.

---

## 🚢 Deployment

### Docker Compose (Production)

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### پارس‌پک (PaaS)

راهنمای کامل در [PARSPACK_DEPLOY.md](PARSPACK_DEPLOY.md)

### سرور Dedicated

راهنمای کامل در [DEPLOYMENT.md](deployment/DEPLOYMENT.md)

---

## 🤝 مشارکت

مشارکت شما خوشحال‌مان می‌کند! لطفاً:

1. Fork کنید
2. Branch جدید بسازید (`git checkout -b feature/AmazingFeature`)
3. Commit کنید (`git commit -m 'Add some AmazingFeature'`)
4. Push کنید (`git push origin feature/AmazingFeature`)
5. Pull Request بزنید

### کد استایل

- **Python**: PEP 8
- **JavaScript**: ESLint
- **Commits**: Conventional Commits

---

## 📝 لایسنس

این پروژه تحت لایسنس MIT منتشر شده است - فایل [LICENSE](LICENSE) را ببینید.

---

## 👥 نویسندگان

- **توسعه‌دهنده اصلی** - [نام شما](https://github.com/your-username)

---

## 🙏 تشکر

- [FastAPI](https://fastapi.tiangolo.com) - وب فریم‌ورک
- [OpenAI](https://openai.com) - Whisper API
- [SQLAlchemy](https://sqlalchemy.org) - ORM
- [Pydantic](https://pydantic-docs.helpmanual.io) - Validation

---

## 📞 پشتیبانی

- 📧 Email: support@example.com
- 💬 Telegram: @your_channel
- 🐛 Issues: [GitHub Issues](https://github.com/your-username/AI-Hospital/issues)

---

**ساخته شده با ❤️ برای پرستاران ایرانی**
