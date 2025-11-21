from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship, foreign

from ..db import Base
from .user_company import user_company_table


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    address = Column(String(512), nullable=True)
    legal_person = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)

    # Backrefs
    vendors = relationship("User", secondary=user_company_table, back_populates="customer_companies")
    members = relationship(
        "Customer",
        primaryjoin="Company.id == foreign(Customer.company_id)",
        foreign_keys="Customer.company_id",
        viewonly=True,
    )
    departments = relationship("Department", back_populates="company", cascade="all, delete-orphan")
    # linked_departments removed with partner companies feature.
