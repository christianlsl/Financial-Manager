from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class SaleBase(BaseModel):
    date: date
    company_id: int | None = None
    type_id: int | None = None
    item_name: str | None = None
    items_count: int
    total_price: Decimal
    status: str = "draft"
    notes: Optional[str] = None


class SaleCreate(SaleBase):
    pass


class SaleUpdate(BaseModel):
    date: Optional[date] = None
    company_id: Optional[int] = None
    type_id: Optional[int] = None
    item_name: Optional[str] = None
    items_count: Optional[int] = None
    total_price: Optional[Decimal] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class SaleRead(SaleBase):
    id: int
    # Pydantic v2 style config
    model_config = ConfigDict(from_attributes=True)
