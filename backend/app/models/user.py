"""
================================================================================
مدل کاربر (User)
================================================================================
این مدل اطلاعات کاربران (پرستاران) را در دیتابیس ذخیره می‌کند.

فیلدها:
- اطلاعات شخصی: نام، نام خانوادگی، ایمیل، شماره پرسنلی
- احراز هویت: رمز عبور (hash شده)
- نقش: نقش کاربر در سیستم (پرستار، سرپرستار، مدیر)
- وضعیت: فعال/غیرفعال
- timestamps: زمان ایجاد و آپدیت
================================================================================
"""

from datetime import datetime
from typing import Optional, List
from enum import Enum
from sqlalchemy import String, Boolean, DateTime, Enum as SQLEnum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


# ========================================
# Enum برای نقش کاربران
# ========================================

class UserRole(str, Enum):
    """
    نقش‌های مختلف کاربران در سیستم
    
    - NURSE: پرستار عادی (دسترسی به ثبت و مشاهده گزارشات خود)
    - HEAD_NURSE: سرپرستار (دسترسی به مشاهده گزارشات تیم)
    - ADMIN: مدیر سیستم (دسترسی کامل)
    """
    NURSE = "nurse"
    HEAD_NURSE = "head_nurse"
    ADMIN = "admin"


# ========================================
# مدل User
# ========================================

class User(Base):
    """
    مدل کاربر (پرستار) در سیستم
    
    این مدل اطلاعات کاربران را ذخیره می‌کند و relation به مدل Report دارد.
    
    Attributes:
        id: شناسه یکتای کاربر (UUID)
        employee_code: شماره پرسنلی
        first_name: نام
        last_name: نام خانوادگی
        email: ایمیل (یکتا)
        phone_number: شماره تلفن (اختیاری)
        hashed_password: رمز عبور hash شده
        role: نقش کاربر
        is_active: وضعیت فعال/غیرفعال
        department: بخش بیمارستان (اختیاری)
        bio: توضیحات اضافی (اختیاری)
        last_login: آخرین ورود به سیستم
        created_at: زمان ایجاد
        updated_at: زمان آخرین آپدیت
    """
    
    __tablename__ = "users"
    
    # ========================================
    # Primary Key
    # ========================================
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="شناسه یکتای کاربر (UUID)"
    )
    
    # ========================================
    # اطلاعات شخصی
    # ========================================
    employee_code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
        comment="شماره پرسنلی (یکتا)"
    )
    
    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="نام"
    )
    
    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="نام خانوادگی"
    )
    
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="ایمیل (یکتا)"
    )
    
    phone_number: Mapped[Optional[str]] = mapped_column(
        String(15),
        nullable=True,
        comment="شماره تلفن"
    )
    
    # ========================================
    # احراز هویت
    # ========================================
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="رمز عبور hash شده با bcrypt"
    )
    
    # ========================================
    # نقش و دسترسی
    # ========================================
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole),
        default=UserRole.NURSE,
        nullable=False,
        comment="نقش کاربر در سیستم"
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="وضعیت فعال/غیرفعال"
    )
    
    # ========================================
    # اطلاعات تکمیلی
    # ========================================
    department: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="بخش بیمارستان"
    )
    
    bio: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="توضیحات اضافی درباره کاربر"
    )
    
    # ========================================
    # Timestamps
    # ========================================
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="آخرین ورود به سیستم"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="زمان ایجاد"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="زمان آخرین آپدیت"
    )
    
    # ========================================
    # Relationships
    # ========================================
    # رابطه با مدل Report (یک کاربر می‌تواند چندین گزارش داشته باشد)
    # این relation بعداً در مدل Report تعریف می‌شود
      # ========================================
    # Relationships
    # - reports: گزارش‌هایی که این کاربر (پرستار) ثبت کرده
    # - reviewed_reports: گزارش‌هایی که این کاربر به عنوان بررسی‌کننده ثبت کرده
    # ========================================
    reports: Mapped[List["Report"]] = relationship(
        "Report",
        back_populates="nurse",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    reviewed_reports: Mapped[List["Report"]] = relationship(
        "Report",
        back_populates="reviewer",
        foreign_keys='Report.reviewed_by_id',
        lazy="selectin"
    )

    
    # ========================================
    # Methods
    # ========================================
    
    def __repr__(self) -> str:
        """نمایش string از object"""
        return (
            f"<User(id={self.id}, "
            f"employee_code={self.employee_code}, "
            f"name={self.full_name}, "
            f"role={self.role})>"
        )
    
    @property
    def full_name(self) -> str:
        """نام کامل کاربر"""
        return f"{self.first_name} {self.last_name}"
    
    def is_admin(self) -> bool:
        """آیا کاربر ادمین است؟"""
        return self.role == UserRole.ADMIN
    
    def is_head_nurse(self) -> bool:
        """آیا کاربر سرپرستار است؟"""
        return self.role == UserRole.HEAD_NURSE
    
    def can_manage_reports(self) -> bool:
        """آیا کاربر می‌تواند گزارشات را مدیریت کند؟"""
        return self.role in [UserRole.ADMIN, UserRole.HEAD_NURSE]
    
    def to_dict(self) -> dict:
        """تبدیل object به dictionary (بدون password)"""
        return {
            "id": self.id,
            "employee_code": self.employee_code,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "email": self.email,
            "phone_number": self.phone_number,
            "role": self.role.value,
            "is_active": self.is_active,
            "department": self.department,
            "bio": self.bio,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


# ========================================
# Export
# ========================================
__all__ = ["User", "UserRole"]
