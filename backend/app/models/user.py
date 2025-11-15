from sqlalchemy import Boolean, Column, DateTime, Integer, String, func
from sqlalchemy.orm import relationship

from ..db import Base
from .user_customer import user_customer_table
from .user_company import user_company_table


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)

    company_name = Column(String(255), nullable=True)
    customer_companies = relationship(
        "Company",
        secondary=user_company_table,
        back_populates="vendors",
    )

    customers = relationship(
        "Customer",
        secondary=user_customer_table,
        back_populates="vendors",
    )

    purchases = relationship("Purchase", back_populates="owner", cascade="all, delete-orphan")
    sales = relationship("Sale", back_populates="owner", cascade="all, delete-orphan")
    types = relationship("Type", back_populates="owner", cascade="all, delete-orphan")
