"""
================================================================================
API v1 - Main Router
================================================================================
این فایل تمام routers نسخه 1 API را یکجا می‌کند.
================================================================================
"""

from fastapi import APIRouter

from app.api.v1 import auth, reports


# ========================================
# Main API Router v1
# ========================================
api_router = APIRouter(prefix="/v1")

# Include sub-routers
api_router.include_router(auth.router)
api_router.include_router(reports.router)


# ========================================
# Export
# ========================================
__all__ = ["api_router"]
