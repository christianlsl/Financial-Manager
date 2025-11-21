from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class DepartmentBase(BaseModel):
    name: str
    company_id: int


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    company_id: Optional[int] = None


class DepartmentRead(DepartmentBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
