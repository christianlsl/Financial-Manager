from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class SaleBase(BaseModel):
    date: date
    type_id: int | None = None
    customer_id: int
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
    date: Optional[date] = None
    type_id: Optional[int] = None
    customer_id: Optional[int] = None
    item_name: Optional[str] = None
    items_count: Optional[int] = None
    unit_price: Optional[Decimal] = None
    total_price: Optional[Decimal] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    image_url: Optional[str] = None


class SaleRead(SaleBase):
    id: int
    # Pydantic v2 style config
    model_config = ConfigDict(from_attributes=True)


class SaleList(BaseModel):
    items: list[SaleRead]
    total: int


class SaleImageUploadResponse(BaseModel):
    url: str
