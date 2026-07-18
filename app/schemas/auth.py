"""Auth-related Pydantic schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    nickname: str = Field(min_length=2, max_length=64)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    password_confirm: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserOut(BaseModel):
    id: int
    email: EmailStr
    nickname: str
    total_distance: int = 0
    total_duration: int = 0
    total_cleaned_count: int = 0
    total_score: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}