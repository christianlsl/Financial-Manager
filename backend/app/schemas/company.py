from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict


class CompanyBase(BaseModel):
    name: str
    address: Optional[str] = None
    legal_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    legal_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None


class CompanyRead(CompanyBase):
    id: int
    # Pydantic v2 style config
    model_config = ConfigDict(from_attributes=True)
