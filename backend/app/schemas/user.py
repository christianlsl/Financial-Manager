from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict, Field


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    company_name: str
    enc_password: str  # RSA-encrypted password (base64)


class UserRead(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    company_name: str | None = Field(default=None, validation_alias="company")
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class UserProfileUpdate(BaseModel):
    email: EmailStr | None = None
    company_name: str | None = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    enc_password: str


class ChangePasswordRequest(BaseModel):
    enc_current_password: str
    enc_new_password: str
