"""
================================================================================
Schemas برای User (Pydantic Models)
================================================================================
این فایل مدل‌های Pydantic برای validation و serialization کاربران را تعریف می‌کند.

استفاده:
- UserCreate: برای ثبت‌نام کاربر جدید
- UserLogin: برای ورود کاربر
- UserUpdate: برای آپدیت اطلاعات
- UserResponse: برای نمایش اطلاعات کاربر
================================================================================
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator
from app.models.user import UserRole


# ========================================
# Base Schema (مشترک)
# ========================================

class UserBase(BaseModel):
    """
    Schema پایه برای User
    حاوی فیلدهای مشترک بین تمام schemas
    """
    email: EmailStr = Field(
        ...,
        description="ایمیل کاربر",
        example="nurse@hospital.com"
    )
    first_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="نام",
        example="فاطمه"
    )
    last_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="نام خانوادگی",
        example="احمدی"
    )
    phone_number: Optional[str] = Field(
        None,
        pattern=r"^09\d{9}$",
        description="شماره موبایل (فرمت: 09123456789)",
        example="09123456789"
    )
    department: Optional[str] = Field(
        None,
        max_length=100,
        description="بخش بیمارستان",
        example="ICU"
    )


# ========================================
# Create Schema (برای ثبت‌نام)
# ========================================

class UserCreate(UserBase):
    """
    Schema برای ایجاد کاربر جدید
    
    استفاده در endpoint: POST /api/v1/auth/register
    """
    employee_code: str = Field(
        ...,
        min_length=3,
        max_length=20,
        description="شماره پرسنلی",
        example="NUR001"
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="رمز عبور (حداقل 8 کاراکتر)",
        example="SecurePass123!"
    )
    role: UserRole = Field(
        default=UserRole.NURSE,
        description="نقش کاربر در سیستم"
    )
    
    @validator("password")
    def validate_password_strength(cls, v):
        """
        اعتبارسنجی قدرت رمز عبور
        
        الزامات:
        - حداقل 8 کاراکتر
        - حداقل یک حرف بزرگ
        - حداقل یک حرف کوچک
        - حداقل یک عدد
        """
        if len(v) < 8:
            raise ValueError("رمز عبور باید حداقل 8 کاراکتر باشد")
        
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError(
                "رمز عبور باید شامل حروف بزرگ، کوچک و عدد باشد"
            )
        
        return v
    
    @validator("employee_code")
    def validate_employee_code(cls, v):
        """اعتبارسنجی کد پرسنلی"""
        if not v.isalnum():
            raise ValueError("کد پرسنلی فقط باید شامل حروف و اعداد باشد")
        return v.upper()


# ========================================
# Login Schema (برای ورود)
# ========================================

class UserLogin(BaseModel):
    """
    Schema برای ورود کاربر
    
    استفاده در endpoint: POST /api/v1/auth/login
    """
    email: EmailStr = Field(
        ...,
        description="ایمیل کاربر",
        example="nurse@hospital.com"
    )
    password: str = Field(
        ...,
        description="رمز عبور",
        example="SecurePass123!"
    )


# ========================================
# Update Schema (برای آپدیت)
# ========================================

class UserUpdate(BaseModel):
    """
    Schema برای آپدیت اطلاعات کاربر
    
    همه فیلدها اختیاری هستند
    استفاده در endpoint: PUT /api/v1/users/{user_id}
    """
    first_name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=100,
        description="نام"
    )
    last_name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=100,
        description="نام خانوادگی"
    )
    email: Optional[EmailStr] = Field(
        None,
        description="ایمیل"
    )
    phone_number: Optional[str] = Field(
        None,
        pattern=r"^09\d{9}$",
        description="شماره موبایل"
    )
    department: Optional[str] = Field(
        None,
        max_length=100,
        description="بخش"
    )
    bio: Optional[str] = Field(
        None,
        max_length=500,
        description="توضیحات"
    )


# ========================================
# Response Schema (برای نمایش)
# ========================================

class UserResponse(UserBase):
    """
    Schema برای نمایش اطلاعات کاربر
    
    استفاده در response تمام endpoints
    """
    id: str = Field(..., description="شناسه یکتای کاربر")
    employee_code: str = Field(..., description="شماره پرسنلی")
    role: UserRole = Field(..., description="نقش کاربر")
    is_active: bool = Field(..., description="وضعیت فعال/غیرفعال")
    bio: Optional[str] = Field(None, description="توضیحات")
    last_login: Optional[datetime] = Field(None, description="آخرین ورود")
    created_at: datetime = Field(..., description="زمان ایجاد")
    updated_at: datetime = Field(..., description="زمان آپدیت")
    
    class Config:
        """تنظیمات Pydantic"""
        from_attributes = True  # برای خواندن از ORM models
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "employee_code": "NUR001",
                "email": "nurse@hospital.com",
                "first_name": "فاطمه",
                "last_name": "احمدی",
                "phone_number": "09123456789",
                "department": "ICU",
                "role": "nurse",
                "is_active": True,
                "bio": "پرستار بخش مراقبت‌های ویژه",
                "last_login": "2024-11-19T10:30:00Z",
                "created_at": "2024-01-15T08:00:00Z",
                "updated_at": "2024-11-19T10:30:00Z"
            }
        }


# ========================================
# Password Change Schema
# ========================================

class PasswordChange(BaseModel):
    """
    Schema برای تغییر رمز عبور
    
    استفاده در endpoint: POST /api/v1/users/change-password
    """
    old_password: str = Field(
        ...,
        description="رمز عبور فعلی",
        example="OldPass123!"
    )
    new_password: str = Field(
        ...,
        min_length=8,
        description="رمز عبور جدید",
        example="NewPass123!"
    )
    
    @validator("new_password")
    def validate_password_strength(cls, v, values):
        """اعتبارسنجی رمز عبور جدید"""
        if len(v) < 8:
            raise ValueError("رمز عبور باید حداقل 8 کاراکتر باشد")
        
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError(
                "رمز عبور باید شامل حروف بزرگ، کوچک و عدد باشد"
            )
        
        # بررسی اینکه رمز جدید با قدیمی یکی نباشد
        if "old_password" in values and v == values["old_password"]:
            raise ValueError("رمز عبور جدید نباید با رمز قدیمی یکسان باشد")
        
        return v


# ========================================
# Token Response Schema
# ========================================

class TokenResponse(BaseModel):
    """
    Schema برای پاسخ token
    
    استفاده در endpoint: POST /api/v1/auth/login
    """
    access_token: str = Field(..., description="Access Token")
    refresh_token: str = Field(..., description="Refresh Token")
    token_type: str = Field(default="bearer", description="نوع Token")
    expires_in: int = Field(..., description="مدت اعتبار (ثانیه)")
    user: UserResponse = Field(..., description="اطلاعات کاربر")
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800,
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "employee_code": "NUR001",
                    "email": "nurse@hospital.com",
                    "first_name": "فاطمه",
                    "last_name": "احمدی",
                    "role": "nurse",
                    "is_active": True
                }
            }
        }


# ========================================
# Export
# ========================================
__all__ = [
    "UserBase",
    "UserCreate",
    "UserLogin",
    "UserUpdate",
    "UserResponse",
    "PasswordChange",
    "TokenResponse",
]
