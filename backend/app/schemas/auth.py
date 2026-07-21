"""Pydantic schemas for authentication endpoints."""

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """POST /api/auth/login — request body"""
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    """POST /api/auth/register — request body (admin-only invite)"""
    email: EmailStr
    password: str
    role: str = "member"  # "admin" or "member"


class TokenResponse(BaseModel):
    """Response containing JWT tokens"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """POST /api/auth/refresh — request body"""
    refresh_token: str
