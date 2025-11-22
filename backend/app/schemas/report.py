"""
================================================================================
Schemas برای Report (Pydantic Models)
================================================================================
این فایل مدل‌های Pydantic برای validation و serialization گزارشات را تعریف می‌کند.
================================================================================
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator
from app.models.report import ReportStatus, ReportType


# ========================================
# Base Schema
# ========================================

class ReportBase(BaseModel):
    """Schema پایه برای Report"""
    patient_name: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="نام و نام خانوادگی بیمار",
        example="علی محمدی"
    )
    patient_national_id: Optional[str] = Field(
        None,
        pattern=r"^\d{10}$",
        description="کد ملی بیمار (10 رقم)",
        example="1234567890"
    )
    patient_file_number: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="شماره پرونده بیمار",
        example="P-2024-001"
    )
    content: str = Field(
        ...,
        min_length=10,
        description="محتوای گزارش",
        example="بیمار در وضعیت پایدار است. علائم حیاتی طبیعی..."
    )
    notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="یادداشت‌های اضافی"
    )


# ========================================
# Create Schema
# ========================================

class ReportCreate(ReportBase):
    """
    Schema برای ایجاد گزارش جدید
    
    استفاده: POST /api/v1/reports
    """
    report_type: ReportType = Field(
        default=ReportType.TEXT,
        description="نوع گزارش"
    )
    
    @validator("patient_file_number")
    def validate_file_number(cls, v):
        """اعتبارسنجی شماره پرونده"""
        return v.strip().upper()


# ========================================
# Voice Upload Schema
# ========================================

class VoiceReportCreate(BaseModel):
    """
    Schema برای ایجاد گزارش صوتی
    
    استفاده: POST /api/v1/reports/voice
    
    Note: فایل صوتی از طریق multipart/form-data ارسال می‌شود
    """
    patient_name: str = Field(..., description="نام بیمار")
    patient_national_id: Optional[str] = Field(None, description="کد ملی")
    patient_file_number: str = Field(..., description="شماره پرونده")
    notes: Optional[str] = Field(None, description="یادداشت")


# ========================================
# Update Schema
# ========================================

class ReportUpdate(BaseModel):
    """
    Schema برای آپدیت گزارش
    
    همه فیلدها اختیاری
    """
    patient_name: Optional[str] = Field(None, min_length=2, max_length=200)
    patient_national_id: Optional[str] = Field(None, pattern=r"^\d{10}$")
    patient_file_number: Optional[str] = Field(None, min_length=1, max_length=50)
    content: Optional[str] = Field(None, min_length=10)
    notes: Optional[str] = Field(None, max_length=1000)
    status: Optional[ReportStatus] = Field(None, description="وضعیت گزارش")


# ========================================
# Response Schema
# ========================================

class ReportResponse(ReportBase):
    """
    Schema برای نمایش گزارش
    """
    id: str = Field(..., description="شناسه گزارش")
    nurse_id: str = Field(..., description="شناسه پرستار")
    nurse_name: Optional[str] = Field(None, description="نام پرستار")
    report_type: ReportType = Field(..., description="نوع گزارش")
    status: ReportStatus = Field(..., description="وضعیت گزارش")
    
    # اطلاعات فایل صوتی
    audio_file_path: Optional[str] = Field(None, description="مسیر فایل")
    audio_duration: Optional[float] = Field(None, description="مدت زمان (ثانیه)")
    audio_duration_formatted: Optional[str] = Field(None, description="مدت زمان فرمت شده")
    audio_size: Optional[int] = Field(None, description="حجم (بایت)")
    audio_size_formatted: Optional[str] = Field(None, description="حجم فرمت شده")
    
    # اطلاعات تبدیل
    is_transcribed: bool = Field(..., description="آیا تبدیل شده؟")
    transcription_confidence: Optional[float] = Field(
        None,
        ge=0,
        le=1,
        description="میزان اطمینان"
    )
    
    # اطلاعات بررسی
    reviewed_by_id: Optional[str] = Field(None, description="بررسی‌کننده")
    reviewed_at: Optional[datetime] = Field(None, description="زمان بررسی")
    
    # Timestamps
    created_at: datetime = Field(..., description="زمان ایجاد")
    updated_at: datetime = Field(..., description="زمان آپدیت")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "rep-123",
                "nurse_id": "usr-456",
                "nurse_name": "فاطمه احمدی",
                "patient_name": "علی محمدی",
                "patient_national_id": "1234567890",
                "patient_file_number": "P-2024-001",
                "report_type": "voice",
                "content": "بیمار در وضعیت پایدار است...",
                "status": "final",
                "is_transcribed": True,
                "transcription_confidence": 0.95,
                "created_at": "2024-11-19T10:00:00Z",
                "updated_at": "2024-11-19T10:00:00Z"
            }
        }


# ========================================
# List Response
# ========================================

class ReportListResponse(BaseModel):
    """
    Schema برای لیست گزارشات (با pagination)
    """
    items: list[ReportResponse] = Field(..., description="لیست گزارشات")
    total: int = Field(..., description="تعداد کل")
    page: int = Field(..., description="صفحه فعلی")
    page_size: int = Field(..., description="تعداد در صفحه")
    total_pages: int = Field(..., description="تعداد کل صفحات")
    
    class Config:
        json_schema_extra = {
            "example": {
                "items": [],
                "total": 100,
                "page": 1,
                "page_size": 10,
                "total_pages": 10
            }
        }


# ========================================
# Statistics Schema
# ========================================

class ReportStatistics(BaseModel):
    """
    آمار گزارشات
    """
    total_reports: int = Field(..., description="تعداد کل گزارشات")
    draft_reports: int = Field(..., description="پیش‌نویس‌ها")
    final_reports: int = Field(..., description="گزارشات نهایی")
    reviewed_reports: int = Field(..., description="بررسی شده‌ها")
    voice_reports: int = Field(..., description="گزارشات صوتی")
    text_reports: int = Field(..., description="گزارشات متنی")
    today_reports: int = Field(..., description="گزارشات امروز")
    this_week_reports: int = Field(..., description="گزارشات این هفته")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_reports": 150,
                "draft_reports": 10,
                "final_reports": 120,
                "reviewed_reports": 90,
                "voice_reports": 80,
                "text_reports": 70,
                "today_reports": 5,
                "this_week_reports": 25
            }
        }


# ========================================
# Export
# ========================================
__all__ = [
    "ReportBase",
    "ReportCreate",
    "VoiceReportCreate",
    "ReportUpdate",
    "ReportResponse",
    "ReportListResponse",
    "ReportStatistics",
]
