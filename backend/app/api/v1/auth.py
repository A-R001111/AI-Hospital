"""
================================================================================
Authentication Router
================================================================================
API endpoints برای احراز هویت:
- POST /register: ثبت‌نام کاربر جدید
- POST /login: ورود و دریافت token
- POST /refresh: تمدید token
- GET /me: اطلاعات کاربر فعلی
================================================================================
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse
)
from app.services.auth_service import AuthService


# ========================================
# Router
# ========================================
router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


# ========================================
# Register
# ========================================
@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="ثبت‌نام کاربر جدید",
    description="""
    ثبت‌نام یک کاربر جدید در سیستم.
    
    **الزامات:**
    - ایمیل باید یکتا باشد
    - کد پرسنلی باید یکتا باشد
    - رمز عبور باید حداقل 8 کاراکتر و شامل حروف بزرگ، کوچک و عدد باشد
    
    **نمونه درخواست:**
    ```json
    {
        "employee_code": "NUR001",
        "first_name": "فاطمه",
        "last_name": "احمدی",
        "email": "nurse@hospital.com",
        "phone_number": "09123456789",
        "password": "SecurePass123!",
        "role": "nurse",
        "department": "ICU"
    }
    ```
    """
)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    ثبت‌نام کاربر جدید
    
    Args:
        user_data: اطلاعات کاربر
        db: database session
        
    Returns:
        UserResponse: اطلاعات کاربر ایجاد شده
        
    Raises:
        HTTPException 400: اگر ایمیل یا کد پرسنلی تکراری باشد
    """
    user = await AuthService.register_user(user_data, db)
    return UserResponse.model_validate(user)


# ========================================
# Login
# ========================================
@router.post(
    "/login",
    response_model=TokenResponse,
    summary="ورود به سیستم",
    description="""
    ورود کاربر و دریافت JWT tokens.
    
    **نمونه درخواست:**
    ```json
    {
        "email": "nurse@hospital.com",
        "password": "SecurePass123!"
    }
    ```
    
    **پاسخ شامل:**
    - access_token: برای دسترسی به API ها (معتبر برای 30 دقیقه)
    - refresh_token: برای تمدید access token (معتبر برای 7 روز)
    - user: اطلاعات کاربر
    """
)
async def login(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """
    ورود کاربر
    
    Args:
        login_data: ایمیل و رمز عبور
        db: database session
        
    Returns:
        TokenResponse: tokens و اطلاعات کاربر
        
    Raises:
        HTTPException 401: اگر ایمیل یا رمز اشتباه باشد
        HTTPException 403: اگر حساب غیرفعال باشد
    """
    return await AuthService.login_user(login_data, db)


# ========================================
# Refresh Token
# ========================================
@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="تمدید Token",
    description="""
    تمدید access token با استفاده از refresh token.
    
    **نمونه درخواست:**
    ```json
    {
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
    ```
    """
)
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """
    تمدید access token
    
    Args:
        refresh_token: refresh token
        db: database session
        
    Returns:
        TokenResponse: tokens جدید
        
    Raises:
        HTTPException 401: اگر refresh token نامعتبر باشد
    """
    return await AuthService.refresh_token(refresh_token, db)


# ========================================
# Get Current User (Me)
# ========================================
@router.get(
    "/me",
    response_model=UserResponse,
    summary="اطلاعات کاربر فعلی",
    description="""
    دریافت اطلاعات کاربر فعلی از طریق JWT token.
    
    **نیاز به Authentication:**
    - Header: `Authorization: Bearer <access_token>`
    """
)
async def get_me(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """
    دریافت اطلاعات کاربر فعلی
    
    Args:
        current_user: کاربر فعلی (از token)
        
    Returns:
        UserResponse: اطلاعات کاربر
    """
    return UserResponse.model_validate(current_user)


# ========================================
# Logout (Optional)
# ========================================
@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="خروج از سیستم",
    description="""
    خروج از سیستم.
    
    **نکته:** در معماری JWT stateless، logout در سمت client انجام می‌شود
    (حذف token). این endpoint صرفاً برای logging و tracking است.
    """
)
async def logout(
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    خروج از سیستم
    
    Args:
        current_user: کاربر فعلی
        
    Returns:
        dict: پیام موفقیت
    """
    return {
        "message": "با موفقیت خارج شدید",
        "user_id": current_user.id
    }


# ========================================
# Health Check (برای این router)
# ========================================
@router.get(
    "/health",
    summary="بررسی سلامت Authentication",
    include_in_schema=False  # در docs نمایش داده نشود
)
async def auth_health():
    """بررسی سلامت سرویس authentication"""
    return {
        "status": "healthy",
        "service": "authentication"
    }
