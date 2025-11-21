from sqlalchemy import Column, Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship
from .type import Type  # noqa: F401
from .supplier import Supplier  # noqa: F401

from ..db import Base


class PurchaseStatusEnum(str):
    PENDING = "pending"
    ORDERED = "ordered"
    RECEIVED = "received"


class Purchase(Base):
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    type_id = Column(Integer, ForeignKey("types.id", ondelete="SET NULL"), nullable=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True, index=True)
    item_name = Column(String(255), nullable=True)
    items_count = Column(Integer, nullable=False, default=0)
    unit_price = Column(Numeric(12, 2), nullable=False, default=0)
    total_price = Column(Numeric(12, 2), nullable=False, default=0)
    image_url = Column(String(512), nullable=True)
    status = Column(String(50), nullable=False, default=PurchaseStatusEnum.PENDING)
    notes = Column(Text, nullable=True)

    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    owner = relationship("User", back_populates="purchases")
    type = relationship("Type", back_populates="purchases")
    supplier = relationship("Supplier", back_populates="purchases")
