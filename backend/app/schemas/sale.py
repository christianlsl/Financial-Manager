from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class SaleBase(BaseModel):
    date: dt.date
    type_id: int | None = None
    customer_id: int | None = None
    item_name: str | None = None
    items_count: int
    unit_price: Decimal
    total_price: Decimal
    status: str = "draft"
    notes: Optional[str] = None
    image_url: Optional[str] = None


class SaleCreate(SaleBase):
    pass


class SaleUpdate(BaseModel):
    date: dt.date | None = None
    type_id: Optional[int] = None
    customer_id: Optional[int] = None
    item_name: Optional[str] = None
    items_count: Optional[int] = None
    unit_price: Optional[Decimal] = None
    total_price: Optional[Decimal] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    image_url: Optional[str] = None


from .department import DepartmentRead


class SaleRead(SaleBase):
    id: int
    customer_department_id: int | None = None
    customer_department: DepartmentRead | None = None
    company_name: str | None = None
    department_name: str | None = None
    customer_name: str | None = None
    type_name: str | None = None
    # Pydantic v2 style config
    model_config = ConfigDict(from_attributes=True)


class SaleList(BaseModel):
    items: list[SaleRead]
    total: int


class SaleImageUploadResponse(BaseModel):
    url: str
