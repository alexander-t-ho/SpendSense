"""Pydantic models for SpendSense API."""

from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    username: str  # Email or username
    password: str


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: Dict[str, Any]


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    username: Optional[str]
    is_admin: bool

