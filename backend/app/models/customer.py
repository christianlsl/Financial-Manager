from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship, foreign

from ..db import Base
from .user_customer import user_customer_table


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    phone_number = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    position = Column(String(255), nullable=True)
    company_id = Column(Integer, nullable=False, default=0, index=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)

    company = relationship(
        "Company",
        primaryjoin="Company.id == foreign(Customer.company_id)",
        foreign_keys=[company_id],
        viewonly=True,
    )
    department = relationship("Department", foreign_keys=[department_id], back_populates="members")
    sales = relationship("Sale", back_populates="customer")
    vendors = relationship("User", secondary=user_customer_table, back_populates="customers")
