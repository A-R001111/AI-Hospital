"""
================================================================================
Authentication Service
================================================================================
این سرویس تمام منطق business مربوط به احراز هویت را مدیریت می‌کند:
- ثبت‌نام کاربر جدید
- ورود و صدور token
- تمدید token
- تغییر رمز عبور
================================================================================
"""

from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, TokenResponse, PasswordChange
from app.core.security import (
    hash_password,
    verify_password,
    create_tokens_pair,
    check_password_strength
)


class AuthService:
    """
    سرویس احراز هویت
    
    تمام عملیات مربوط به authentication در این کلاس مدیریت می‌شود.
    """
    
    @staticmethod
    async def register_user(
        user_data: UserCreate,
        db: AsyncSession
    ) -> User:
        """
        ثبت‌نام کاربر جدید
        
        مراحل:
        1. بررسی عدم تکراری بودن email و employee_code
        2. بررسی قدرت password
        3. Hash کردن password
        4. ذخیره در دیتابیس
        
        Args:
            user_data: اطلاعات کاربر جدید
            db: session دیتابیس
            
        Returns:
            User: کاربر ایجاد شده
            
        Raises:
            HTTPException: در صورت وجود email یا employee_code تکراری
        """
        # بررسی ایمیل تکراری
        result = await db.execute(
            select(User).where(User.email == user_data.email)
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="این ایمیل قبلاً ثبت شده است"
            )
        
        # بررسی کد پرسنلی تکراری
        result = await db.execute(
            select(User).where(User.employee_code == user_data.employee_code)
        )
        existing_code = result.scalar_one_or_none()
        
        if existing_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="این کد پرسنلی قبلاً ثبت شده است"
            )
        
        # Hash کردن password
        hashed_password = hash_password(user_data.password)
        
        # ایجاد کاربر جدید
        new_user = User(
            employee_code=user_data.employee_code,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            email=user_data.email,
            phone_number=user_data.phone_number,
            hashed_password=hashed_password,
            role=user_data.role,
            department=user_data.department,
            is_active=True
        )
        
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        return new_user
    
    @staticmethod
    async def login_user(
        login_data: UserLogin,
        db: AsyncSession
    ) -> TokenResponse:
        """
        ورود کاربر و صدور token
        
        مراحل:
        1. یافتن کاربر با email
        2. بررسی صحت password
        3. بررسی فعال بودن کاربر
        4. صدور access و refresh token
        5. ثبت زمان ورود
        
        Args:
            login_data: اطلاعات ورود (email, password)
            db: session دیتابیس
            
        Returns:
            TokenResponse: حاوی tokens و اطلاعات کاربر
            
        Raises:
            HTTPException: در صورت اشتباه بودن email یا password
        """
        # یافتن کاربر
        result = await db.execute(
            select(User).where(User.email == login_data.email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="ایمیل یا رمز عبور اشتباه است",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # بررسی password
        if not verify_password(login_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="ایمیل یا رمز عبور اشتباه است",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # بررسی فعال بودن
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="حساب کاربری شما غیرفعال شده است"
            )
        
        # ثبت زمان ورود
        user.last_login = datetime.utcnow()
        await db.commit()
        
        # صدور tokens
        tokens = create_tokens_pair(user.id)
        
        # ایجاد response
        from app.schemas.user import UserResponse
        user_response = UserResponse.model_validate(user)
        
        return TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type=tokens["token_type"],
            expires_in=tokens["expires_in"],
            user=user_response
        )
    
    @staticmethod
    async def get_current_user(
        user_id: str,
        db: AsyncSession
    ) -> User:
        """
        دریافت اطلاعات کاربر فعلی از طریق user_id
        
        این متد برای dependency injection در endpoints استفاده می‌شود.
        
        Args:
            user_id: شناسه کاربر (از token استخراج می‌شود)
            db: session دیتابیس
            
        Returns:
            User: اطلاعات کاربر
            
        Raises:
            HTTPException: اگر کاربر یافت نشود
        """
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="کاربر یافت نشد",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="حساب کاربری غیرفعال است"
            )
        
        return user
    
    @staticmethod
    async def change_password(
        user_id: str,
        password_data: PasswordChange,
        db: AsyncSession
    ) -> dict:
        """
        تغییر رمز عبور کاربر
        
        مراحل:
        1. یافتن کاربر
        2. بررسی صحت رمز فعلی
        3. بررسی قدرت رمز جدید
        4. Hash و ذخیره رمز جدید
        
        Args:
            user_id: شناسه کاربر
            password_data: رمز فعلی و جدید
            db: session دیتابیس
            
        Returns:
            dict: پیام موفقیت
            
        Raises:
            HTTPException: در صورت اشتباه بودن رمز فعلی
        """
        # یافتن کاربر
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="کاربر یافت نشد"
            )
        
        # بررسی رمز فعلی
        if not verify_password(password_data.old_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="رمز عبور فعلی اشتباه است"
            )
        
        # Hash کردن رمز جدید
        new_hashed_password = hash_password(password_data.new_password)
        
        # ذخیره
        user.hashed_password = new_hashed_password
        await db.commit()
        
        return {"message": "رمز عبور با موفقیت تغییر کرد"}
    
    @staticmethod
    async def refresh_token(
        refresh_token: str,
        db: AsyncSession
    ) -> TokenResponse:
        """
        تمدید access token با استفاده از refresh token
        
        Args:
            refresh_token: refresh token ارسال شده
            db: session دیتابیس
            
        Returns:
            TokenResponse: tokens جدید
            
        Raises:
            HTTPException: اگر refresh token نامعتبر باشد
        """
        from app.core.security import decode_token
        
        # decode کردن refresh token
        try:
            payload = decode_token(refresh_token)
        except HTTPException:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="refresh token نامعتبر است"
            )
        
        # بررسی نوع token
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="نوع token اشتباه است"
            )
        
        user_id = payload.get("sub")
        
        # دریافت کاربر
        user = await AuthService.get_current_user(user_id, db)
        
        # صدور tokens جدید
        tokens = create_tokens_pair(user.id)
        
        from app.schemas.user import UserResponse
        user_response = UserResponse.model_validate(user)
        
        return TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type=tokens["token_type"],
            expires_in=tokens["expires_in"],
            user=user_response
        )


# ========================================
# Export
# ========================================
__all__ = ["AuthService"]
