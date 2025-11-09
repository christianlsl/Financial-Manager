from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from ..db import Base
from .user_customer import user_customer_table


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    address = Column(String(512), nullable=True)
    legal_person = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)

    # Backrefs
    members = relationship("User", back_populates="company", foreign_keys="User.company_id")
    owners = relationship("User", secondary=user_customer_table, back_populates="customer_companies")
    purchases = relationship("Purchase", back_populates="company")
    sales = relationship("Sale", back_populates="company")
