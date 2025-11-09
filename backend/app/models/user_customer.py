from sqlalchemy import Column, ForeignKey, Integer, Table

from ..db import Base

user_customer_table = Table(
    "user_customers",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("company_id", ForeignKey("companies.id", ondelete="CASCADE"), primary_key=True),
)
