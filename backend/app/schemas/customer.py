from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr


class CustomerBase(BaseModel):
    name: str
    phone_number: Optional[str] = None
    email: Optional[str] = None
    position: Optional[str] = None
    company_id: int
    department_id: Optional[int] = None


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    position: Optional[str] = None
    company_id: Optional[int] = None


class CustomerRead(CustomerBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class CustomerGroup(BaseModel):
    company_id: int
    customers: list[CustomerRead]
