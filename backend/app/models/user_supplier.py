from sqlalchemy import Column, ForeignKey, Integer, Table

from ..db import Base

user_supplier_table = Table(
    "user_suppliers",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("supplier_id", ForeignKey("suppliers.id", ondelete="CASCADE"), primary_key=True),
)
