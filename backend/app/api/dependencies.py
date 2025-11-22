"""
================================================================================
Dependencies - Dependency Injection Utilities
================================================================================
این فایل توابع dependency injection برای FastAPI را فراهم می‌کند.

استفاده در API Endpoints:
- get_db: دریافت database session
- get_current_user: دریافت کاربر فعلی از token
- require_role: محدودیت دسترسی بر اساس نقش
================================================================================
"""

from typing import AsyncGenerator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker
from app.core.security import decode_token
from app.models.user import User, UserRole
from app.services.auth_service import AuthService


# ========================================
# Security Scheme
# ========================================
security = HTTPBearer(
    scheme_name="JWT Authentication",
    description="JWT Bearer Token Authentication"
)


# ========================================
# Database Session Dependency
# ========================================
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency برای دریافت database session
    
    این dependency در هر endpoint که به دیتابیس نیاز دارد استفاده می‌شود.
    
    استفاده:
    ```python
    @app.get("/users")
    async def get_users(db: AsyncSession = Depends(get_db)):
        # استفاده از db
    ```
    
    Yields:
        AsyncSession: session دیتابیس
    """
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


# ========================================
# Current User Dependency
# ========================================
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency برای دریافت کاربر فعلی از JWT token
    
    مراحل:
    1. استخراج token از header
    2. Decode و validation token
    3. دریافت user_id از payload
    4. Query کاربر از دیتابیس
    5. بررسی فعال بودن
    
    استفاده:
    ```python
    @app.get("/profile")
    async def get_profile(
        current_user: User = Depends(get_current_user)
    ):
        return current_user
    ```
    
    Args:
        credentials: JWT token از header
        db: database session
        
    Returns:
        User: کاربر فعلی
        
    Raises:
        HTTPException: اگر token نامعتبر یا کاربر یافت نشود
    """
    # استخراج token
    token = credentials.credentials
    
    # Decode token
    try:
        payload = decode_token(token)
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="توکن نامعتبر یا منقضی شده است",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # بررسی نوع token (باید access باشد)
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="نوع توکن اشتباه است",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # استخراج user_id
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="توکن نامعتبر است",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # دریافت کاربر از دیتابیس
    user = await AuthService.get_current_user(user_id, db)
    
    return user


# ========================================
# Optional User Dependency
# ========================================
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Dependency برای دریافت کاربر فعلی (اختیاری)
    
    اگر token ارسال نشده باشد، None برمی‌گرداند.
    برای endpoint‌هایی که authentication اختیاری است.
    
    استفاده:
    ```python
    @app.get("/public-data")
    async def get_public_data(
        current_user: Optional[User] = Depends(get_current_user_optional)
    ):
        if current_user:
            # نمایش داده‌های شخصی‌سازی شده
        else:
            # نمایش داده‌های عمومی
    ```
    
    Args:
        credentials: JWT token از header (اختیاری)
        db: database session
        
    Returns:
        Optional[User]: کاربر یا None
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


# ========================================
# Role-Based Access Control
# ========================================
class RoleChecker:
    """
    کلاس برای بررسی نقش کاربر
    
    استفاده:
    ```python
    @app.post("/admin/users")
    async def create_user(
        current_user: User = Depends(RoleChecker([UserRole.ADMIN]))
    ):
        # فقط admin می‌تواند اجرا کند
    ```
    """
    
    def __init__(self, allowed_roles: list[UserRole]):
        """
        Args:
            allowed_roles: لیست نقش‌های مجاز
        """
        self.allowed_roles = allowed_roles
    
    def __call__(
        self,
        current_user: User = Depends(get_current_user)
    ) -> User:
        """
        بررسی نقش کاربر
        
        Args:
            current_user: کاربر فعلی
            
        Returns:
            User: کاربر در صورت داشتن دسترسی
            
        Raises:
            HTTPException: اگر کاربر دسترسی نداشته باشد
        """
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="شما دسترسی به این عملیات را ندارید"
            )
        
        return current_user


# ========================================
# Predefined Role Checkers
# ========================================

# فقط Admin
require_admin = RoleChecker([UserRole.ADMIN])

# فقط Doctor
require_doctor = RoleChecker([UserRole.DOCTOR])

# فقط Nurse
require_nurse = RoleChecker([UserRole.NURSE])

# Doctor یا Admin
require_doctor_or_admin = RoleChecker([UserRole.DOCTOR, UserRole.ADMIN])

# Nurse یا Doctor
require_nurse_or_doctor = RoleChecker([UserRole.NURSE, UserRole.DOCTOR])

# هر کاربر احراز هویت شده
require_authenticated = get_current_user


# ========================================
# Pagination Dependency
# ========================================
class PaginationParams:
    """
    کلاس برای pagination parameters
    
    استفاده:
    ```python
    @app.get("/items")
    async def get_items(
        pagination: PaginationParams = Depends()
    ):
        skip = (pagination.page - 1) * pagination.page_size
        limit = pagination.page_size
        # query با skip و limit
    ```
    """
    
    def __init__(
        self,
        page: int = 1,
        page_size: int = 10
    ):
        """
        Args:
            page: شماره صفحه (از 1 شروع می‌شود)
            page_size: تعداد آیتم‌ها در هر صفحه
        """
        # اعتبارسنجی
        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="شماره صفحه باید حداقل 1 باشد"
            )
        
        if page_size < 1 or page_size > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="تعداد آیتم در صفحه باید بین 1 تا 100 باشد"
            )
        
        self.page = page
        self.page_size = page_size
    
    @property
    def skip(self) -> int:
        """محاسبه skip برای query"""
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        """محاسبه limit برای query"""
        return self.page_size


# ========================================
# Export
# ========================================
__all__ = [
    "get_db",
    "get_current_user",
    "get_current_user_optional",
    "RoleChecker",
    "require_admin",
    "require_doctor",
    "require_nurse",
    "require_doctor_or_admin",
    "require_nurse_or_doctor",
    "require_authenticated",
    "PaginationParams",
]
