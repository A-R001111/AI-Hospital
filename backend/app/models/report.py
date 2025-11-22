"""
================================================================================
مدل گزارش پرستاری (Report)
================================================================================
این مدل گزارش‌های پرستاران را در دیتابیس ذخیره می‌کند.

فیلدها:
- اطلاعات بیمار: نام، کد ملی، شماره پرونده
- محتوای گزارش: متن گزارش (تبدیل شده از صدا یا ورودی دستی)
- اطلاعات فایل صوتی: مسیر، مدت زمان، سایز
- وضعیت: پیش‌نویس، نهایی، تایید شده
- timestamps و metadata
================================================================================
"""

from datetime import datetime
from typing import Optional
from enum import Enum
from sqlalchemy import (
    String, Text, Integer, Float, Boolean, 
    DateTime, Enum as SQLEnum, ForeignKey
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


# ========================================
# Enum برای وضعیت گزارش
# ========================================

class ReportStatus(str, Enum):
    """
    وضعیت‌های مختلف گزارش
    
    - DRAFT: پیش‌نویس (در حال ویرایش)
    - FINAL: نهایی (تکمیل شده توسط پرستار)
    - REVIEWED: بررسی شده (توسط سرپرستار)
    - ARCHIVED: بایگانی شده
    """
    DRAFT = "draft"
    FINAL = "final"
    REVIEWED = "reviewed"
    ARCHIVED = "archived"


class ReportType(str, Enum):
    """
    نوع گزارش
    
    - VOICE: گزارش ثبت شده با صدا
    - TEXT: گزارش نوشته شده دستی
    - MIXED: ترکیبی از صدا و متن
    """
    VOICE = "voice"
    TEXT = "text"
    MIXED = "mixed"


# ========================================
# مدل Report
# ========================================

class Report(Base):
    """
    مدل گزارش پرستاری
    
    این مدل اطلاعات گزارش‌های پرستاران را ذخیره می‌کند.
    هر گزارش به یک پرستار (User) متصل است.
    
    Attributes:
        id: شناسه یکتای گزارش (UUID)
        nurse_id: شناسه پرستار ثبت‌کننده
        patient_name: نام بیمار
        patient_national_id: کد ملی بیمار
        patient_file_number: شماره پرونده بیمار
        report_type: نوع گزارش (صوتی/متنی)
        content: محتوای متنی گزارش
        audio_file_path: مسیر فایل صوتی
        audio_duration: مدت زمان صدا (ثانیه)
        audio_size: حجم فایل صوتی (بایت)
        status: وضعیت گزارش
        is_transcribed: آیا تبدیل صدا به متن انجام شده؟
        transcription_confidence: میزان اطمینان از تبدیل
        notes: یادداشت‌های اضافی
        reviewed_by_id: شناسه بررسی‌کننده
        reviewed_at: زمان بررسی
        created_at: زمان ایجاد
        updated_at: زمان آخرین آپدیت
    """
    
    __tablename__ = "reports"
    
    # ========================================
    # Primary Key
    # ========================================
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="شناسه یکتای گزارش (UUID)"
    )
    
    # ========================================
    # Foreign Keys
    # ========================================
    nurse_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="شناسه پرستار ثبت‌کننده"
    )
    
    reviewed_by_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="شناسه بررسی‌کننده گزارش"
    )
    
    # ========================================
    # اطلاعات بیمار
    # ========================================
    patient_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="نام و نام خانوادگی بیمار"
    )
    
    patient_national_id: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        index=True,
        comment="کد ملی بیمار (10 رقم)"
    )
    
    patient_file_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="شماره پرونده بیمار"
    )
    
    # ========================================
    # نوع و محتوای گزارش
    # ========================================
    report_type: Mapped[ReportType] = mapped_column(
        SQLEnum(ReportType),
        nullable=False,
        comment="نوع گزارش (صوتی/متنی/ترکیبی)"
    )
    
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="محتوای متنی گزارش"
    )
    
    # ========================================
    # اطلاعات فایل صوتی
    # ========================================
    audio_file_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="مسیر فایل صوتی در سرور"
    )
    
    audio_duration: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="مدت زمان صدا (ثانیه)"
    )
    
    audio_size: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="حجم فایل صوتی (بایت)"
    )
    
    # ========================================
    # اطلاعات تبدیل صدا به متن
    # ========================================
    is_transcribed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="آیا صدا به متن تبدیل شده؟"
    )
    
    transcription_confidence: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="میزان اطمینان از تبدیل (0 تا 1)"
    )
    
    # ========================================
    # وضعیت و metadata
    # ========================================
    status: Mapped[ReportStatus] = mapped_column(
        SQLEnum(ReportStatus),
        default=ReportStatus.DRAFT,
        nullable=False,
        index=True,
        comment="وضعیت گزارش"
    )
    
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="یادداشت‌های اضافی"
    )
    
    # ========================================
    # Timestamps
    # ========================================
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="زمان بررسی گزارش"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="زمان ایجاد گزارش"
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
    # رابطه با User (پرستار ثبت‌کننده)
    nurse: Mapped["User"] = relationship(
        "User",
        foreign_keys=[nurse_id],
        back_populates="reports",
        lazy="selectin"  # eager loading
    )
    
    # رابطه با User (بررسی‌کننده)
    reviewer: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[reviewed_by_id],
        lazy="selectin"
    )
    
    # ========================================
    # Methods
    # ========================================
    
    def __repr__(self) -> str:
        """نمایش string از object"""
        return (
            f"<Report(id={self.id}, "
            f"patient={self.patient_name}, "
            f"type={self.report_type}, "
            f"status={self.status})>"
        )
    
    def is_editable(self) -> bool:
        """آیا گزارش قابل ویرایش است؟"""
        return self.status in [ReportStatus.DRAFT, ReportStatus.FINAL]
    
    def can_be_archived(self) -> bool:
        """آیا گزارش قابل بایگانی است؟"""
        return self.status == ReportStatus.REVIEWED
    
    def mark_as_final(self) -> None:
        """تبدیل گزارش به وضعیت نهایی"""
        if self.status == ReportStatus.DRAFT:
            self.status = ReportStatus.FINAL
    
    def mark_as_reviewed(self, reviewer_id: str) -> None:
        """ثبت بررسی گزارش"""
        self.status = ReportStatus.REVIEWED
        self.reviewed_by_id = reviewer_id
        self.reviewed_at = datetime.utcnow()
    
    def get_duration_formatted(self) -> Optional[str]:
        """دریافت مدت زمان به فرمت قابل خواندن"""
        if not self.audio_duration:
            return None
        
        minutes = int(self.audio_duration // 60)
        seconds = int(self.audio_duration % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def get_size_formatted(self) -> Optional[str]:
        """دریافت حجم فایل به فرمت قابل خواندن"""
        if not self.audio_size:
            return None
        
        # تبدیل به KB یا MB
        if self.audio_size < 1024 * 1024:  # کمتر از 1MB
            return f"{self.audio_size / 1024:.1f} KB"
        else:
            return f"{self.audio_size / (1024 * 1024):.1f} MB"
    
    def to_dict(self) -> dict:
        """تبدیل object به dictionary"""
        return {
            "id": self.id,
            "nurse_id": self.nurse_id,
            "nurse_name": self.nurse.full_name if self.nurse else None,
            "patient_name": self.patient_name,
            "patient_national_id": self.patient_national_id,
            "patient_file_number": self.patient_file_number,
            "report_type": self.report_type.value,
            "content": self.content,
            "audio_file_path": self.audio_file_path,
            "audio_duration": self.audio_duration,
            "audio_duration_formatted": self.get_duration_formatted(),
            "audio_size": self.audio_size,
            "audio_size_formatted": self.get_size_formatted(),
            "is_transcribed": self.is_transcribed,
            "transcription_confidence": self.transcription_confidence,
            "status": self.status.value,
            "notes": self.notes,
            "reviewed_by_id": self.reviewed_by_id,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


# ========================================
# Export
# ========================================
__all__ = ["Report", "ReportStatus", "ReportType"]
