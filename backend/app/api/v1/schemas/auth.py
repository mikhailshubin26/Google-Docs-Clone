# pydantic-схемы запросов/ответов для auth-эндпоинтов

from pydantic import BaseModel, EmailStr, Field

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=255)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class GuestLoginRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=255)

class UpgradeGuestRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class RefreshRequest(BaseModel):
    refresh_token: str

class TokenPairResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"