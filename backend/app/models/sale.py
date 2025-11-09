from sqlalchemy import Column, Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship
from .company import Company  # noqa: F401
from .type import Type  # noqa: F401

from ..db import Base


class SaleStatusEnum(str):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"


class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True)
    type_id = Column(Integer, ForeignKey("types.id", ondelete="SET NULL"), nullable=True, index=True)
    item_name = Column(String(255), nullable=True)
    items_count = Column(Integer, nullable=False, default=0)
    total_price = Column(Numeric(12, 2), nullable=False, default=0)
    status = Column(String(50), nullable=False, default=SaleStatusEnum.DRAFT)
    notes = Column(Text, nullable=True)

    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    owner = relationship("User", back_populates="sales")
    company = relationship("Company", back_populates="sales")
    type = relationship("Type", back_populates="sales")
