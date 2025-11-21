from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship, foreign

from ..db import Base
from .user_supplier import user_supplier_table


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    phone_number = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    address = Column(String(255), nullable=True)

    purchases = relationship("Purchase", back_populates="supplier")
    customers = relationship("User", secondary=user_supplier_table, back_populates="suppliers")
