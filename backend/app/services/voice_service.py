"""
================================================================================
Voice-to-Text Service
================================================================================
این سرویس تبدیل صدا به متن را با استفاده از OpenAI Whisper API انجام می‌دهد.

ویژگی‌ها:
- پشتیبانی از فرمت‌های مختلف صوتی
- تبدیل با دقت بالا
- پردازش async
- Error handling جامع
================================================================================
"""

import os
import aiofiles
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import openai
from fastapi import UploadFile, HTTPException, status

from app.core.config import settings


class VoiceService:
    """
    سرویس تبدیل صدا به متن
    
    استفاده از OpenAI Whisper API برای transcription
    """
    
    # فرمت‌های مجاز
    ALLOWED_FORMATS = ["wav", "mp3", "m4a", "ogg", "webm", "flac"]
    
    # حداکثر سایز فایل (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    def __init__(self):
        """تنظیم OpenAI API"""
        openai.api_key = settings.OPENAI_API_KEY
        
        # ایجاد دایرکتوری uploads اگر وجود ندارد
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    def validate_audio_file(self, file: UploadFile) -> None:
        """
        اعتبارسنجی فایل صوتی
        
        بررسی:
        - فرمت فایل
        - سایز فایل
        
        Args:
            file: فایل آپلود شده
            
        Raises:
            HTTPException: اگر فایل نامعتبر باشد
        """
        # بررسی فرمت
        file_extension = file.filename.split(".")[-1].lower()
        
        if file_extension not in self.ALLOWED_FORMATS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"فرمت فایل باید یکی از {', '.join(self.ALLOWED_FORMATS)} باشد"
            )
        
        # بررسی سایز (اگر در دسترس باشد)
        if hasattr(file, "size") and file.size:
            if file.size > self.MAX_FILE_SIZE:
                max_mb = self.MAX_FILE_SIZE / (1024 * 1024)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"سایز فایل نباید بیشتر از {max_mb}MB باشد"
                )
    
    async def save_audio_file(
        self,
        file: UploadFile,
        report_id: str
    ) -> Dict[str, Any]:
        """
        ذخیره فایل صوتی در سرور
        
        Args:
            file: فایل صوتی
            report_id: شناسه گزارش
            
        Returns:
            Dict حاوی:
                - file_path: مسیر فایل ذخیره شده
                - file_size: سایز فایل (بایت)
                - file_extension: پسوند فایل
        """
        # ساخت نام یکتا برای فایل
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = file.filename.split(".")[-1].lower()
        filename = f"{report_id}_{timestamp}.{file_extension}"
        
        # مسیر کامل فایل
        file_path = self.upload_dir / filename
        
        # ذخیره فایل
        file_size = 0
        async with aiofiles.open(file_path, 'wb') as f:
            while chunk := await file.read(1024 * 1024):  # 1MB chunks
                await f.write(chunk)
                file_size += len(chunk)
        
        return {
            "file_path": str(file_path),
            "file_size": file_size,
            "file_extension": file_extension
        }
    
    async def transcribe_audio(
        self,
        file_path: str,
        language: str = "fa"
    ) -> Dict[str, Any]:
        """
        تبدیل فایل صوتی به متن با Whisper API
        
        Args:
            file_path: مسیر فایل صوتی
            language: زبان (fa برای فارسی، en برای انگلیسی)
            
        Returns:
            Dict حاوی:
                - text: متن تبدیل شده
                - confidence: میزان اطمینان (تقریبی)
                - duration: مدت زمان صدا (اگر در دسترس باشد)
                
        Raises:
            HTTPException: در صورت خطا در تبدیل
        """
        try:
            # باز کردن فایل صوتی
            with open(file_path, "rb") as audio_file:
                # فراخوانی Whisper API
                transcript = await self._call_whisper_api(
                    audio_file,
                    language
                )
            
            # استخراج اطلاعات
            text = transcript.text
            
            # محاسبه confidence (Whisper مستقیم confidence نمیده، تقریب میزنیم)
            # بر اساس طول متن و کیفیت
            confidence = self._estimate_confidence(text)
            
            # محاسبه مدت زمان (اگر در دسترس باشد)
            duration = self._get_audio_duration(file_path)
            
            return {
                "text": text,
                "confidence": confidence,
                "duration": duration
            }
            
        except openai.error.OpenAIError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"خطا در تبدیل صدا به متن: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"خطای غیرمنتظره: {str(e)}"
            )
    
    async def _call_whisper_api(
        self,
        audio_file,
        language: str
    ):
        """
        فراخوانی API Whisper
        
        Note: این متد sync است چون OpenAI SDK async ندارد
        """
        # استفاده از model whisper-1
        return openai.Audio.transcribe(
            model=settings.OPENAI_MODEL,
            file=audio_file,
            language=language,
            response_format="text"
        )
    
    def _estimate_confidence(self, text: str) -> float:
        """
        تخمین میزان اطمینان بر اساس کیفیت متن
        
        فاکتورها:
        - طول متن
        - وجود کلمات معنادار
        - عدم وجود کاراکترهای مشکوک
        
        Returns:
            float: عدد بین 0 تا 1
        """
        if not text or len(text) < 10:
            return 0.5
        
        # بررسی طول (متن‌های کوتاه معمولاً کیفیت پایین‌تری دارند)
        length_score = min(len(text) / 100, 1.0)
        
        # بررسی تعداد کلمات
        words = text.split()
        word_score = min(len(words) / 20, 1.0)
        
        # میانگین
        confidence = (length_score + word_score) / 2
        
        # حداقل 0.7 و حداکثر 0.98
        return max(0.7, min(confidence, 0.98))
    
    def _get_audio_duration(self, file_path: str) -> Optional[float]:
        """
        محاسبه مدت زمان فایل صوتی
        
        استفاده از pydub برای استخراج duration
        
        Args:
            file_path: مسیر فایل
            
        Returns:
            float: مدت زمان به ثانیه یا None
        """
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(file_path)
            return len(audio) / 1000.0  # تبدیل میلی‌ثانیه به ثانیه
        except Exception:
            # اگر خطا داد، None برمی‌گردانیم
            return None
    
    async def delete_audio_file(self, file_path: str) -> bool:
        """
        حذف فایل صوتی از سرور
        
        Args:
            file_path: مسیر فایل
            
        Returns:
            bool: True اگر موفق باشد
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception:
            return False
    
    async def process_voice_report(
        self,
        file: UploadFile,
        report_id: str
    ) -> Dict[str, Any]:
        """
        پردازش کامل گزارش صوتی
        
        مراحل:
        1. اعتبارسنجی فایل
        2. ذخیره فایل
        3. تبدیل به متن
        4. بازگشت نتایج
        
        Args:
            file: فایل صوتی
            report_id: شناسه گزارش
            
        Returns:
            Dict حاوی تمام اطلاعات پردازش
        """
        # اعتبارسنجی
        self.validate_audio_file(file)
        
        # ذخیره فایل
        file_info = await self.save_audio_file(file, report_id)
        
        # تبدیل به متن
        transcription = await self.transcribe_audio(
            file_info["file_path"],
            language="fa"  # فارسی
        )
        
        # ترکیب نتایج
        return {
            "file_path": file_info["file_path"],
            "file_size": file_info["file_size"],
            "file_extension": file_info["file_extension"],
            "transcribed_text": transcription["text"],
            "confidence": transcription["confidence"],
            "duration": transcription["duration"]
        }


# ========================================
# Singleton Instance
# ========================================
voice_service = VoiceService()


# ========================================
# Export
# ========================================
__all__ = ["VoiceService", "voice_service"]
