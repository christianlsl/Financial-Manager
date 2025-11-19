import os
import stat
from datetime import date, timedelta
from decimal import Decimal

from ..core.config import settings
from ..db import Base, engine, SessionLocal
from ..core.security import get_password_hash

# Import models so they are registered with Base metadata
from ..models import company  # noqa: F401
from ..models import user  # noqa: F401
from ..models import purchase  # noqa: F401
from ..models import sale  # noqa: F401
from ..models import type  # noqa: F401
from ..models.user import User
from ..models.company import Company
from ..models.customer import Customer
from ..models.type import Type
from ..models.purchase import Purchase
from ..models.sale import Sale


def reset_sqlite_db() -> None:
    db_path = settings.SQLITE_DB_PATH

    if os.path.exists(db_path):
        os.remove(db_path)
    Base.metadata.create_all(bind=engine)
    os.chmod(db_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP)


def seed_sample_data() -> None:
    """Seed the SQLite database with a small set of demo data.

    Creates:
    - 2 users with passwords: "secret"
    - 2 companies and 3 customers
    - 2 types per user
    - 2 purchases and 2 sales with simple totals
    """
    db = SessionLocal()
    try:
        # Users
        alice = User(
            email="1@qq.com",
            hashed_password=get_password_hash("123456"),
            company_name="Alice Trading Co.",
        )
        bob = User(
            email="bob@example.com",
            hashed_password=get_password_hash("123456"),
            company_name="Bob Supplies Ltd.",
        )
        db.add_all([alice, bob])
        db.flush()

        # Companies
        acme = Company(name="Acme Corp", address="1 Road St", legal_person="Wile E.", phone="111-222-3333")
        globex = Company(name="Globex Inc", address="99 Main Ave", legal_person="Hank S.", phone="222-333-4444")
        db.add_all([acme, globex])
        db.flush()

        # Customers (some linked to companies, one standalone company_id=0)
        cust_jane = Customer(name="Jane Doe", phone_number="123456", email="jane@acme.com", position="Manager", company_id=0)
        cust_mike = Customer(name="Mike Smith", phone_number="654321", email="mike@globex.com", position="Buyer", company_id=globex.id)
        cust_ann = Customer(name="Ann Brown", phone_number="888999", email="ann@acme.com", position="CTO", company_id=acme.id)
        db.add_all([cust_jane, cust_mike, cust_ann])
        db.flush()

        # Relations: vendor <-> companies/customers
        alice.customer_companies.extend([acme, globex])
        alice.customers.extend([cust_jane, cust_mike])
        bob.customer_companies.extend([globex])
        bob.customers.extend([cust_ann])

        # Types per user
        t_office_a = Type(name="Office", owner_id=alice.id)
        t_electr_a = Type(name="Electronics", owner_id=alice.id)
        t_services_b = Type(name="Services", owner_id=bob.id)
        t_misc_b = Type(name="Misc", owner_id=bob.id)
        db.add_all([t_office_a, t_electr_a, t_services_b, t_misc_b])
        db.flush()

        today = date.today()

        # Purchases
        p1 = Purchase(
            date=today - timedelta(days=10),
            type_id=t_office_a.id,
            customer_id=cust_mike.id,
            item_name="Printer Paper",
            items_count=10,
            unit_price=Decimal("15.50"),
            total_price=Decimal("155.00"),
            image_url=None,
            notes="Bulk order",
            owner_id=alice.id,
        )
        p2 = Purchase(
            date=today - timedelta(days=5),
            type_id=t_services_b.id,
            customer_id=cust_ann.id,
            item_name="Consulting",
            items_count=2,
            unit_price=Decimal("500.00"),
            total_price=Decimal("1000.00"),
            image_url="https://example.com/invoice1.jpg",
            notes="Retainer",
            owner_id=bob.id,
        )

        # Sales
        s1 = Sale(
            date=today - timedelta(days=7),
            type_id=t_electr_a.id,
            customer_id=cust_ann.id,
            item_name="Monitors",
            items_count=4,
            unit_price=Decimal("199.99"),
            total_price=Decimal("799.96"),
            image_url="https://example.com/receipt1.jpg",
            notes="Delivered",
            owner_id=alice.id,
        )
        s2 = Sale(
            date=today - timedelta(days=2),
            type_id=t_misc_b.id,
            customer_id=cust_jane.id,
            item_name="Accessories",
            items_count=3,
            unit_price=Decimal("25.00"),
            total_price=Decimal("75.00"),
            image_url=None,
            notes="Pick-up",
            owner_id=bob.id,
        )

        db.add_all([p1, p2, s1, s2])
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    reset_sqlite_db()
    seed_sample_data()
    print("Database reset and sample data inserted.")
