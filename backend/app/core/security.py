"""
================================================================================
ماژول امنیت و احراز هویت
================================================================================
این ماژول مسئول تولید و اعتبارسنجی JWT token، hash کردن پسورد،
و مدیریت authentication است.

استفاده از:
- python-jose برای JWT
- passlib برای password hashing
- bcrypt برای الگوریتم hashing
================================================================================
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings


# ========================================
# تنظیمات Password Hashing
# ========================================
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # تعداد rounds برای افزایش امنیت
)

# ========================================
# تنظیمات Bearer Token
# ========================================
security = HTTPBearer()


# ========================================
# توابع Password Hashing
# ========================================

def hash_password(password: str) -> str:
    """
    Hash کردن پسورد با bcrypt
    
    Args:
        password: پسورد Plain Text
        
    Returns:
        str: پسورد Hash شده
        
    Example:
        >>> hashed = hash_password("MySecurePass123")
        >>> print(hashed)
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    مقایسه پسورد Plain Text با Hash شده
    
    Args:
        plain_password: پسورد وارد شده توسط کاربر
        hashed_password: پسورد Hash شده در دیتابیس
        
    Returns:
        bool: True اگر پسورد صحیح باشد
        
    Example:
        >>> is_valid = verify_password("MyPass", hashed_password)
        >>> print(is_valid)
    """
    return pwd_context.verify(plain_password, hashed_password)


# ========================================
# توابع JWT Token
# ========================================

def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    ایجاد Access Token برای احراز هویت
    
    Args:
        data: دیکشنری حاوی اطلاعات کاربر (معمولاً user_id)
        expires_delta: مدت زمان اعتبار token (اختیاری)
        
    Returns:
        str: JWT Token رمزنگاری شده
        
    Example:
        >>> token = create_access_token({"sub": "user123"})
        >>> print(token)
    """
    # کپی کردن data برای جلوگیری از تغییر اصل
    to_encode = data.copy()
    
    # تعیین زمان انقضا
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    # افزودن زمان انقضا و issued at به token
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    # رمزنگاری و تولید token
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    ایجاد Refresh Token برای تمدید access token
    
    Args:
        data: دیکشنری حاوی اطلاعات کاربر
        expires_delta: مدت زمان اعتبار (اختیاری)
        
    Returns:
        str: JWT Refresh Token
        
    Example:
        >>> refresh = create_refresh_token({"sub": "user123"})
        >>> print(refresh)
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """
    رمزگشایی و اعتبارسنجی JWT Token
    
    Args:
        token: JWT Token برای رمزگشایی
        
    Returns:
        Dict: محتویات token (payload)
        
    Raises:
        HTTPException: در صورت نامعتبر بودن token
        
    Example:
        >>> payload = decode_token(token)
        >>> user_id = payload.get("sub")
    """
    try:
        # رمزگشایی token
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
        
    except JWTError as e:
        # Token نامعتبر است
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="توکن نامعتبر یا منقضی شده است",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    استخراج user_id از JWT Token
    
    این تابع به عنوان dependency در endpoint ها استفاده می‌شود
    برای احراز هویت کاربر.
    
    Args:
        credentials: اعتبارسنامه Bearer Token از header
        
    Returns:
        str: شناسه کاربر (user_id)
        
    Raises:
        HTTPException: اگر token نامعتبر باشد یا user_id وجود نداشته باشد
        
    Example در endpoint:
        >>> @app.get("/protected")
        >>> async def protected_route(user_id: str = Depends(get_current_user_id)):
        >>>     return {"user_id": user_id}
    """
    token = credentials.credentials
    
    # رمزگشایی token
    payload = decode_token(token)
    
    # استخراج user_id
    user_id: Optional[str] = payload.get("sub")
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="اطلاعات کاربر در توکن یافت نشد",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # بررسی نوع token (باید access باشد)
    token_type = payload.get("type")
    if token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="نوع توکن نامعتبر است",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_id


def create_tokens_pair(user_id: str) -> Dict[str, str]:
    """
    ایجاد هم‌زمان Access Token و Refresh Token
    
    Args:
        user_id: شناسه کاربر
        
    Returns:
        Dict: دیکشنری حاوی access_token و refresh_token
        
    Example:
        >>> tokens = create_tokens_pair("user123")
        >>> print(tokens["access_token"])
        >>> print(tokens["refresh_token"])
    """
    # ایجاد payload مشترک
    token_data = {"sub": user_id}
    
    # تولید هر دو token
    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data=token_data)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # به ثانیه
    }


# ========================================
# توابع Helper برای بررسی دسترسی
# ========================================

def check_password_strength(password: str) -> bool:
    """
    بررسی قدرت پسورد
    
    حداقل الزامات:
    - حداقل 8 کاراکتر
    - حداقل یک حرف بزرگ
    - حداقل یک حرف کوچک
    - حداقل یک عدد
    - حداقل یک کاراکتر ویژه
    
    Args:
        password: پسورد برای بررسی
        
    Returns:
        bool: True اگر پسورد قوی باشد
        
    Example:
        >>> is_strong = check_password_strength("MyPass123!")
        >>> print(is_strong)
    """
    if len(password) < 8:
        return False
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    
    return has_upper and has_lower and has_digit and has_special


# ========================================
# Export
# ========================================
__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "get_current_user_id",
    "create_tokens_pair",
    "check_password_strength",
    "security",
]
