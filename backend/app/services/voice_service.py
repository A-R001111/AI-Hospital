"""
================================================================================
Voice-to-Text Service - نسخه آفلاین
================================================================================
این سرویس از Whisper آفلاین استفاده می‌کند (بدون نیاز به OpenAI API)

ویژگی‌ها:
- استفاده از مدل Whisper آفلاین
- پشتیبانی عالی از فارسی
- کاملاً رایگان
- بدون نیاز به اینترنت برای transcription
================================================================================
"""

import os
import aiofiles
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import whisper
from fastapi import UploadFile, HTTPException, status

from app.core.config import settings


class VoiceService:
    """
    سرویس تبدیل صدا به متن - نسخه آفلاین
    
    استفاده از Whisper local model
    """
    
    # فرمت‌های مجاز
    ALLOWED_FORMATS = ["wav", "mp3", "m4a", "ogg", "webm", "flac"]
    
    # حداکثر سایز فایل (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    def __init__(self):
        """
        تنظیم و بارگذاری مدل Whisper
        
        مدل‌های موجود:
        - tiny: سریع، دقت کم (~1GB RAM)
        - base: متوسط (~1GB RAM) ← پیشنهادی برای شروع
        - small: خوب (~2GB RAM)
        - medium: عالی (~5GB RAM)
        - large: بهترین (~10GB RAM)
        """
        # ایجاد دایرکتوری uploads
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        # بارگذاری مدل Whisper
        # برای شروع از base استفاده می‌کنیم (تعادل خوب بین سرعت و دقت)
        model_size = os.environ.get("WHISPER_MODEL_SIZE", "base")
        
        print(f"🔄 در حال بارگذاری مدل Whisper ({model_size})...")
        try:
            self.model = whisper.load_model(model_size)
            print(f"✅ مدل Whisper بارگذاری شد: {model_size}")
        except Exception as e:
            print(f"❌ خطا در بارگذاری مدل: {e}")
            # اگر مدل لود نشد، به tiny برگرد (کوچک‌ترین)
            print("⚠️ تلاش برای بارگذاری مدل tiny...")
            self.model = whisper.load_model("tiny")
    
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
        
        # بررسی سایز
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
            Dict حاوی اطلاعات فایل
        """
        # ساخت نام یکتا
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = file.filename.split(".")[-1].lower()
        filename = f"{report_id}_{timestamp}.{file_extension}"
        
        # مسیر کامل
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
        تبدیل فایل صوتی به متن با Whisper آفلاین
        
        Args:
            file_path: مسیر فایل صوتی
            language: زبان (fa برای فارسی، en برای انگلیسی)
            
        Returns:
            Dict حاوی:
                - text: متن تبدیل شده
                - confidence: میزان اطمینان
                - duration: مدت زمان صدا
                - language: زبان تشخیص داده شده
                
        Raises:
            HTTPException: در صورت خطا در تبدیل
        """
        try:
            print(f"🔄 شروع transcription: {file_path}")
            
            # Transcribe با Whisper
            result = self.model.transcribe(
                file_path,
                language=language,  # فارسی
                fp16=False,  # برای CPU
                verbose=False
            )
            
            # استخراج اطلاعات
            text = result["text"].strip()
            detected_language = result.get("language", language)
            
            # محاسبه confidence (Whisper مستقیم confidence نمی‌دهد)
            # از میانگین log probabilities استفاده می‌کنیم
            segments = result.get("segments", [])
            if segments:
                # محاسبه میانگین no_speech_prob (هرچه کمتر، بهتر)
                avg_no_speech = sum(s.get("no_speech_prob", 0.5) for s in segments) / len(segments)
                confidence = 1.0 - avg_no_speech  # تبدیل به confidence
            else:
                confidence = 0.8  # مقدار پیش‌فرض
            
            # محاسبه مدت زمان
            duration = self._get_audio_duration_from_segments(segments)
            
            print(f"✅ Transcription موفق: {len(text)} کاراکتر")
            
            return {
                "text": text,
                "confidence": round(confidence, 2),
                "duration": duration,
                "language": detected_language,
                "segments_count": len(segments)
            }
            
        except Exception as e:
            print(f"❌ خطا در transcription: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"خطا در تبدیل صدا به متن: {str(e)}"
            )
    
    def _get_audio_duration_from_segments(self, segments: list) -> Optional[float]:
        """
        محاسبه مدت زمان از segments
        
        Args:
            segments: لیست segments از Whisper
            
        Returns:
            float: مدت زمان به ثانیه
        """
        if not segments:
            return None
        
        # آخرین segment
        last_segment = segments[-1]
        duration = last_segment.get("end", 0)
        
        return round(duration, 2) if duration else None
    
    def _get_audio_duration(self, file_path: str) -> Optional[float]:
        """
        محاسبه مدت زمان فایل صوتی با pydub
        
        Args:
            file_path: مسیر فایل
            
        Returns:
            float: مدت زمان به ثانیه
        """
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(file_path)
            return len(audio) / 1000.0
        except Exception:
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
            "duration": transcription["duration"],
            "language": transcription["language"]
        }


# ========================================
# Singleton Instance
# ========================================
voice_service = VoiceService()


# ========================================
# Export
# ========================================
__all__ = ["VoiceService", "voice_service"]
