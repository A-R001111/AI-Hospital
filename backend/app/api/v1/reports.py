"""
================================================================================
Reports Router
================================================================================
API endpoints برای مدیریت گزارشات:
- POST /: ایجاد گزارش متنی
- POST /voice: ایجاد گزارش صوتی
- GET /: لیست گزارشات
- GET /{report_id}: دریافت یک گزارش
- PUT /{report_id}: ویرایش گزارش
- DELETE /{report_id}: حذف گزارش
- GET /statistics: آمار گزارشات
================================================================================
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_db,
    get_current_user,
    PaginationParams
)
from app.models.user import User
from app.models.report import ReportStatus, ReportType
from app.schemas.report import (
    ReportCreate,
    ReportUpdate,
    VoiceReportCreate,
    ReportResponse,
    ReportListResponse,
    ReportStatistics
)
from app.services.report_service import ReportService


# ========================================
# Router
# ========================================
router = APIRouter(
    prefix="/reports",
    tags=["Reports"]
)


# ========================================
# Create Text Report
# ========================================
@router.post(
    "/",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="ایجاد گزارش متنی",
    description="""
    ایجاد یک گزارش متنی جدید.
    
    **نیاز به Authentication:**
    - باید login کرده باشید
    
    **نمونه درخواست:**
    ```json
    {
        "patient_name": "علی محمدی",
        "patient_national_id": "1234567890",
        "patient_file_number": "P-2024-001",
        "content": "بیمار در وضعیت پایدار است...",
        "notes": "یادداشت اضافی",
        "report_type": "text"
    }
    ```
    """
)
async def create_text_report(
    report_data: ReportCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ReportResponse:
    """
    ایجاد گزارش متنی
    
    Args:
        report_data: اطلاعات گزارش
        current_user: کاربر فعلی
        db: database session
        
    Returns:
        ReportResponse: گزارش ایجاد شده
    """
    report = await ReportService.create_text_report(
        report_data,
        current_user,
        db
    )
    return ReportResponse.model_validate(report)


# ========================================
# Create Voice Report
# ========================================
@router.post(
    "/voice",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="ایجاد گزارش صوتی",
    description="""
    ایجاد گزارش صوتی و تبدیل به متن.
    
    **نحوه ارسال:**
    - نوع: multipart/form-data
    - فیلدها:
        - audio_file: فایل صوتی (wav, mp3, m4a, ...)
        - patient_name: نام بیمار
        - patient_file_number: شماره پرونده
        - patient_national_id: کد ملی (اختیاری)
        - notes: یادداشت (اختیاری)
    
    **فرمت‌های مجاز:**
    - wav, mp3, m4a, ogg, webm, flac
    
    **حداکثر حجم:**
    - 10MB
    """
)
async def create_voice_report(
    audio_file: UploadFile = File(..., description="فایل صوتی"),
    patient_name: str = Form(..., description="نام بیمار"),
    patient_file_number: str = Form(..., description="شماره پرونده"),
    patient_national_id: Optional[str] = Form(None, description="کد ملی"),
    notes: Optional[str] = Form(None, description="یادداشت"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ReportResponse:
    """
    ایجاد گزارش صوتی
    
    Args:
        audio_file: فایل صوتی
        patient_name: نام بیمار
        patient_file_number: شماره پرونده
        patient_national_id: کد ملی
        notes: یادداشت
        current_user: کاربر فعلی
        db: database session
        
    Returns:
        ReportResponse: گزارش ایجاد شده با متن تبدیل شده
    """
    # ساخت schema
    report_data = VoiceReportCreate(
        patient_name=patient_name,
        patient_file_number=patient_file_number,
        patient_national_id=patient_national_id,
        notes=notes
    )
    
    # ایجاد گزارش
    report = await ReportService.create_voice_report(
        audio_file,
        report_data,
        current_user,
        db
    )
    
    return ReportResponse.model_validate(report)


# ========================================
# Get Reports List
# ========================================
@router.get(
    "/",
    response_model=ReportListResponse,
    summary="لیست گزارشات",
    description="""
    دریافت لیست گزارشات کاربر فعلی.
    
    **فیلترها (اختیاری):**
    - status: وضعیت (draft, final, reviewed)
    - type: نوع (text, voice)
    
    **Pagination:**
    - page: شماره صفحه (پیش‌فرض: 1)
    - page_size: تعداد در صفحه (پیش‌فرض: 10، حداکثر: 100)
    """
)
async def get_reports(
    status_filter: Optional[ReportStatus] = None,
    type_filter: Optional[ReportType] = None,
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ReportListResponse:
    """
    دریافت لیست گزارشات
    
    Args:
        status_filter: فیلتر وضعیت
        type_filter: فیلتر نوع
        pagination: پارامترهای pagination
        current_user: کاربر فعلی
        db: database session
        
    Returns:
        ReportListResponse: لیست گزارشات با pagination
    """
    reports, total = await ReportService.get_user_reports(
        current_user,
        db,
        skip=pagination.skip,
        limit=pagination.limit,
        status_filter=status_filter,
        type_filter=type_filter
    )
    
    # محاسبه تعداد صفحات
    total_pages = (total + pagination.page_size - 1) // pagination.page_size
    
    return ReportListResponse(
        items=[ReportResponse.model_validate(r) for r in reports],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages
    )


# ========================================
# Get Single Report
# ========================================
@router.get(
    "/{report_id}",
    response_model=ReportResponse,
    summary="دریافت یک گزارش",
    description="دریافت جزئیات یک گزارش با شناسه"
)
async def get_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ReportResponse:
    """
    دریافت یک گزارش
    
    Args:
        report_id: شناسه گزارش
        current_user: کاربر فعلی
        db: database session
        
    Returns:
        ReportResponse: گزارش
        
    Raises:
        HTTPException 404: اگر گزارش یافت نشود
        HTTPException 403: اگر دسترسی نباشد
    """
    report = await ReportService.get_report_by_id(report_id, db)
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="گزارش یافت نشد"
        )
    
    # بررسی دسترسی
    if report.nurse_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="شما دسترسی به این گزارش را ندارید"
        )
    
    return ReportResponse.model_validate(report)


# ========================================
# Update Report
# ========================================
@router.put(
    "/{report_id}",
    response_model=ReportResponse,
    summary="ویرایش گزارش",
    description="""
    ویرایش یک گزارش موجود.
    
    **محدودیت:**
    - فقط سازنده گزارش یا admin می‌تواند ویرایش کند
    
    **فیلدهای قابل ویرایش:**
    - patient_name
    - patient_national_id
    - patient_file_number
    - content
    - notes
    - status
    """
)
async def update_report(
    report_id: str,
    update_data: ReportUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ReportResponse:
    """
    ویرایش گزارش
    
    Args:
        report_id: شناسه گزارش
        update_data: داده‌های جدید
        current_user: کاربر فعلی
        db: database session
        
    Returns:
        ReportResponse: گزارش ویرایش شده
    """
    report = await ReportService.update_report(
        report_id,
        update_data,
        current_user,
        db
    )
    return ReportResponse.model_validate(report)


# ========================================
# Delete Report
# ========================================
@router.delete(
    "/{report_id}",
    status_code=status.HTTP_200_OK,
    summary="حذف گزارش",
    description="""
    حذف یک گزارش.
    
    **محدودیت:**
    - فقط سازنده گزارش یا admin می‌تواند حذف کند
    
    **نکته:**
    - در صورت وجود فایل صوتی، آن نیز حذف می‌شود
    """
)
async def delete_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    حذف گزارش
    
    Args:
        report_id: شناسه گزارش
        current_user: کاربر فعلی
        db: database session
        
    Returns:
        dict: پیام موفقیت
    """
    return await ReportService.delete_report(report_id, current_user, db)


# ========================================
# Get Statistics
# ========================================
@router.get(
    "/stats/summary",
    response_model=ReportStatistics,
    summary="آمار گزارشات",
    description="""
    دریافت آمار کلی گزارشات کاربر فعلی.
    
    **آمارهای ارائه شده:**
    - تعداد کل گزارشات
    - تعداد پیش‌نویس‌ها
    - تعداد گزارشات نهایی
    - تعداد گزارشات بررسی شده
    - تعداد گزارشات صوتی
    - تعداد گزارشات متنی
    - تعداد گزارشات امروز
    - تعداد گزارشات این هفته
    """
)
async def get_statistics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ReportStatistics:
    """
    دریافت آمار
    
    Args:
        current_user: کاربر فعلی
        db: database session
        
    Returns:
        ReportStatistics: آمار کامل
    """
    return await ReportService.get_statistics(current_user, db)
