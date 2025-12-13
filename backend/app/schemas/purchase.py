from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PurchaseBase(BaseModel):
    date: dt.date
    type_id: int | None = None
    supplier_id: int | None = None
    item_name: str | None = None
    items_count: int
    unit_price: Decimal
    total_price: Decimal
    image_url: Optional[str] = None
    status: str = "pending"
    notes: Optional[str] = None


class PurchaseCreate(PurchaseBase):
    pass


class PurchaseUpdate(BaseModel):
    date: dt.date | None = None
    type_id: Optional[int] = None
    supplier_id: Optional[int] = None
    item_name: Optional[str] = None
    items_count: Optional[int] = None
    unit_price: Optional[Decimal] = None
    total_price: Optional[Decimal] = None
    image_url: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class PurchaseRead(PurchaseBase):
    id: int
    supplier_name: Optional[str] = None
    type_name: Optional[str] = None
    # Pydantic v2 style config
    model_config = ConfigDict(from_attributes=True)


class PurchaseList(BaseModel):
    items: list[PurchaseRead]
    total: int


class PurchaseImageUploadResponse(BaseModel):
    url: str
