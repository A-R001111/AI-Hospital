"""
================================================================================
Report Service
================================================================================
سرویس مدیریت گزارشات پرستاری.

عملیات:
- ایجاد گزارش متنی
- ایجاد گزارش صوتی (با تبدیل به متن)
- ویرایش گزارش
- حذف گزارش
- دریافت لیست گزارشات
- آمار گزارشات
================================================================================
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from fastapi import HTTPException, status, UploadFile

from app.models.report import Report, ReportStatus, ReportType
from app.models.user import User
from app.schemas.report import (
    ReportCreate,
    ReportUpdate,
    VoiceReportCreate,
    ReportStatistics
)
from app.services.voice_service import voice_service


class ReportService:
    """
    سرویس گزارشات
    
    تمام منطق business مربوط به گزارشات در این کلاس است.
    """
    
    @staticmethod
    async def create_text_report(
        report_data: ReportCreate,
        user: User,
        db: AsyncSession
    ) -> Report:
        """
        ایجاد گزارش متنی
        
        Args:
            report_data: اطلاعات گزارش
            user: کاربر ایجادکننده
            db: session دیتابیس
            
        Returns:
            Report: گزارش ایجاد شده
        """
        new_report = Report(
            nurse_id=user.id,
            patient_name=report_data.patient_name,
            patient_national_id=report_data.patient_national_id,
            patient_file_number=report_data.patient_file_number,
            content=report_data.content,
            notes=report_data.notes,
            report_type=report_data.report_type,
            status=ReportStatus.DRAFT,
            is_transcribed=False
        )
        
        db.add(new_report)
        await db.commit()
        await db.refresh(new_report)
        
        return new_report
    
    @staticmethod
    async def create_voice_report(
        audio_file: UploadFile,
        report_data: VoiceReportCreate,
        user: User,
        db: AsyncSession
    ) -> Report:
        """
        ایجاد گزارش صوتی و تبدیل به متن
        
        مراحل:
        1. ایجاد رکورد اولیه در دیتابیس
        2. پردازش فایل صوتی (ذخیره و تبدیل)
        3. آپدیت گزارش با نتایج
        
        Args:
            audio_file: فایل صوتی
            report_data: اطلاعات اولیه گزارش
            user: کاربر ایجادکننده
            db: session دیتابیس
            
        Returns:
            Report: گزارش ایجاد شده
            
        Raises:
            HTTPException: در صورت خطا در پردازش
        """
        # 1. ایجاد رکورد اولیه
        new_report = Report(
            nurse_id=user.id,
            patient_name=report_data.patient_name,
            patient_national_id=report_data.patient_national_id,
            patient_file_number=report_data.patient_file_number,
            content="",  # خالی - بعداً پر می‌شود
            notes=report_data.notes,
            report_type=ReportType.VOICE,
            status=ReportStatus.DRAFT,
            is_transcribed=False
        )
        
        db.add(new_report)
        await db.commit()
        await db.refresh(new_report)
        
        try:
            # 2. پردازش صوت
            voice_result = await voice_service.process_voice_report(
                audio_file,
                new_report.id
            )
            
            # 3. آپدیت گزارش با نتایج
            new_report.content = voice_result["transcribed_text"]
            new_report.audio_file_path = voice_result["file_path"]
            new_report.audio_size = voice_result["file_size"]
            new_report.audio_duration = voice_result["duration"]
            new_report.is_transcribed = True
            new_report.transcription_confidence = voice_result["confidence"]
            
            await db.commit()
            await db.refresh(new_report)
            
            return new_report
            
        except Exception as e:
            # در صورت خطا، گزارش را حذف می‌کنیم
            await db.delete(new_report)
            await db.commit()
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"خطا در پردازش فایل صوتی: {str(e)}"
            )
    
    @staticmethod
    async def get_report_by_id(
        report_id: str,
        db: AsyncSession
    ) -> Optional[Report]:
        """
        دریافت گزارش با ID
        
        Args:
            report_id: شناسه گزارش
            db: session دیتابیس
            
        Returns:
            Optional[Report]: گزارش یا None
        """
        result = await db.execute(
            select(Report).where(Report.id == report_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_report(
        report_id: str,
        update_data: ReportUpdate,
        user: User,
        db: AsyncSession
    ) -> Report:
        """
        ویرایش گزارش
        
        Args:
            report_id: شناسه گزارش
            update_data: داده‌های جدید
            user: کاربر درخواست‌دهنده
            db: session دیتابیس
            
        Returns:
            Report: گزارش ویرایش شده
            
        Raises:
            HTTPException: اگر گزارش یافت نشود یا دسترسی نباشد
        """
        report = await ReportService.get_report_by_id(report_id, db)
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="گزارش یافت نشد"
            )
        
        # بررسی دسترسی (فقط سازنده یا admin)
        if report.nurse_id != user.id and not user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="شما اجازه ویرایش این گزارش را ندارید"
            )
        
        # آپدیت فیلدها
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(report, field, value)
        
        await db.commit()
        await db.refresh(report)
        
        return report
    
    @staticmethod
    async def delete_report(
        report_id: str,
        user: User,
        db: AsyncSession
    ) -> dict:
        """
        حذف گزارش
        
        Args:
            report_id: شناسه گزارش
            user: کاربر درخواست‌دهنده
            db: session دیتابیس
            
        Returns:
            dict: پیام موفقیت
            
        Raises:
            HTTPException: اگر گزارش یافت نشود یا دسترسی نباشد
        """
        report = await ReportService.get_report_by_id(report_id, db)
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="گزارش یافت نشد"
            )
        
        # بررسی دسترسی
        if report.nurse_id != user.id and not user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="شما اجازه حذف این گزارش را ندارید"
            )
        
        # حذف فایل صوتی (اگر وجود دارد)
        if report.audio_file_path:
            await voice_service.delete_audio_file(report.audio_file_path)
        
        # حذف از دیتابیس
        await db.delete(report)
        await db.commit()
        
        return {"message": "گزارش با موفقیت حذف شد"}
    
    @staticmethod
    async def get_user_reports(
        user: User,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 10,
        status_filter: Optional[ReportStatus] = None,
        type_filter: Optional[ReportType] = None
    ) -> Tuple[list[Report], int]:
        """
        دریافت لیست گزارشات کاربر
        
        Args:
            user: کاربر
            db: session دیتابیس
            skip: تعداد skip
            limit: تعداد limit
            status_filter: فیلتر وضعیت (اختیاری)
            type_filter: فیلتر نوع (اختیاری)
            
        Returns:
            Tuple[list[Report], int]: لیست گزارشات و تعداد کل
        """
        # Query پایه
        query = select(Report).where(Report.nurse_id == user.id)
        
        # اعمال فیلترها
        if status_filter:
            query = query.where(Report.status == status_filter)
        
        if type_filter:
            query = query.where(Report.report_type == type_filter)
        
        # مرتب‌سازی (جدیدترین اول)
        query = query.order_by(Report.created_at.desc())
        
        # تعداد کل
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # دریافت گزارشات
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        reports = result.scalars().all()
        
        return list(reports), total
    
    @staticmethod
    async def get_statistics(
        user: User,
        db: AsyncSession
    ) -> ReportStatistics:
        """
        دریافت آمار گزارشات کاربر
        
        Args:
            user: کاربر
            db: session دیتابیس
            
        Returns:
            ReportStatistics: آمار
        """
        base_filter = Report.nurse_id == user.id
        
        # تعداد کل
        total_result = await db.execute(
            select(func.count()).select_from(Report).where(base_filter)
        )
        total_reports = total_result.scalar() or 0
        
        # پیش‌نویس‌ها
        draft_result = await db.execute(
            select(func.count()).select_from(Report).where(
                and_(base_filter, Report.status == ReportStatus.DRAFT)
            )
        )
        draft_reports = draft_result.scalar() or 0
        
        # نهایی‌ها
        final_result = await db.execute(
            select(func.count()).select_from(Report).where(
                and_(base_filter, Report.status == ReportStatus.FINAL)
            )
        )
        final_reports = final_result.scalar() or 0
        
        # بررسی شده‌ها
        reviewed_result = await db.execute(
            select(func.count()).select_from(Report).where(
                and_(base_filter, Report.reviewed_by_id.isnot(None))
            )
        )
        reviewed_reports = reviewed_result.scalar() or 0
        
        # صوتی
        voice_result = await db.execute(
            select(func.count()).select_from(Report).where(
                and_(base_filter, Report.report_type == ReportType.VOICE)
            )
        )
        voice_reports = voice_result.scalar() or 0
        
        # متنی
        text_reports = total_reports - voice_reports
        
        # امروز
        today = datetime.now().date()
        today_result = await db.execute(
            select(func.count()).select_from(Report).where(
                and_(
                    base_filter,
                    func.date(Report.created_at) == today
                )
            )
        )
        today_reports = today_result.scalar() or 0
        
        # این هفته
        week_ago = datetime.now() - timedelta(days=7)
        week_result = await db.execute(
            select(func.count()).select_from(Report).where(
                and_(
                    base_filter,
                    Report.created_at >= week_ago
                )
            )
        )
        this_week_reports = week_result.scalar() or 0
        
        return ReportStatistics(
            total_reports=total_reports,
            draft_reports=draft_reports,
            final_reports=final_reports,
            reviewed_reports=reviewed_reports,
            voice_reports=voice_reports,
            text_reports=text_reports,
            today_reports=today_reports,
            this_week_reports=this_week_reports
        )


# ========================================
# Export
# ========================================
__all__ = ["ReportService"]
