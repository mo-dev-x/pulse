"""Middleware package exports."""

from app.middleware.auth import require_verification

__all__ = ['require_verification']
