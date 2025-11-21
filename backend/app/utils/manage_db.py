import os
import stat
import argparse
from datetime import date, timedelta
from decimal import Decimal

from ..core.config import settings
from ..db import Base, engine, SessionLocal
from ..core.security import get_password_hash

# Import models so they are registered with Base metadata
from ..models import company  # noqa: F401
from ..models import user  # noqa: F401
from ..models import department  # noqa: F401
from ..models import purchase  # noqa: F401
from ..models import sale  # noqa: F401
from ..models import supplier  # noqa: F401
from ..models import type  # noqa: F401
from ..models.user import User
from ..models.company import Company
from ..models.customer import Customer
from ..models.department import Department
from ..models.supplier import Supplier
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
    """Seed the SQLite database with sample data.

    Creates:
    - 2 users with passwords: "123456"
    - Multiple companies, customers, and suppliers
    - Multiple departments
    - Multiple types per user
    - Purchases and 30 sales records with diverse data
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

        # Create more companies
        companies = [
            Company(name="Acme Corp", address="1 Road St", legal_person="Wile E.", phone="111-222-3333"),
            Company(name="Globex Inc", address="99 Main Ave", legal_person="Hank S.", phone="222-333-4444"),
            Company(name="Initech", address="456 Business Ave", legal_person="Bill L.", phone="333-444-5555"),
            Company(name="Umbrella Corp", address="123 Secure St", legal_person="Albert W.", phone="444-555-6666"),
            Company(name="Stark Industries", address="Stark Tower", legal_person="Tony S.", phone="555-666-7777")
        ]
        db.add_all(companies)
        db.flush()

        # Create departments for each company
        departments = []
        for company in companies:
            departments.extend([
                Department(name="Sales", company_id=company.id),
                Department(name="Operations", company_id=company.id),
                Department(name="Finance", company_id=company.id)
            ])
        db.add_all(departments)
        db.flush()

        # Create more customers with proper relationships to users
        # Alice's customers
        alice_customers = [
            Customer(name="Jane Doe", phone_number="123456", email="jane@acme.com", position="Manager", company_id=companies[0].id, department_id=departments[0].id),
            Customer(name="Mike Smith", phone_number="654321", email="mike@globex.com", position="Buyer", company_id=companies[1].id, department_id=departments[4].id),
            Customer(name="Sarah Johnson", phone_number="789012", email="sarah@initech.com", position="Director", company_id=companies[2].id, department_id=departments[6].id),
            Customer(name="Tom Wilson", phone_number="345678", email="tom@umbrella.com", position="Engineer", company_id=companies[0].id, department_id=departments[1].id),
            Customer(name="Lisa Brown", phone_number="901234", email="lisa@stark.com", position="Assistant", company_id=companies[2].id, department_id=departments[7].id)
        ]
        
        # Bob's customers
        bob_customers = [
            Customer(name="Ann Brown", phone_number="888999", email="ann@acme.com", position="CTO", company_id=companies[1].id, department_id=departments[3].id),
            Customer(name="David Lee", phone_number="777888", email="david@initech.com", position="Manager", company_id=companies[3].id, department_id=departments[9].id),
            Customer(name="Emily Davis", phone_number="666777", email="emily@umbrella.com", position="Analyst", company_id=companies[3].id, department_id=departments[10].id),
            Customer(name="Michael Clark", phone_number="555666", email="michael@stark.com", position="Executive", company_id=companies[4].id, department_id=departments[13].id),
            Customer(name="Jennifer White", phone_number="444555", email="jennifer@globex.com", position="Coordinator", company_id=companies[1].id, department_id=departments[5].id)
        ]
        
        all_customers = alice_customers + bob_customers
        db.add_all(all_customers)
        db.flush()

        # Create more suppliers
        suppliers = [
            Supplier(name="Stationery Source", phone_number="555123", email="paper@globex.com", address="Sales"),
            Supplier(name="Logistics Hub", phone_number="555987", email="ops@logistics.com", address="Coordinator"),
            Supplier(name="IT Solutions", phone_number="555456", email="it@solutions.com", address="Technician"),
            Supplier(name="Office Furniture", phone_number="555789", email="furniture@office.com", address="Designer"),
            Supplier(name="Cleaning Services", phone_number="555321", email="cleaning@services.com", address="Manager")
        ]
        db.add_all(suppliers)
        db.flush()

        # Establish proper relations: user -> companies/customers/suppliers
        # SQLAlchemy will automatically handle the reverse relationships
        # Alice's relations
        alice.customer_companies = [companies[0], companies[1], companies[2]]
        alice.customers = alice_customers
        alice.suppliers = [suppliers[0], suppliers[2], suppliers[4]]
        
        # Bob's relations
        bob.customer_companies = [companies[1], companies[3], companies[4]]
        bob.customers = bob_customers
        bob.suppliers = [suppliers[1], suppliers[3]]
        
        # Set owner_id for customers to ensure proper ownership
        for customer in alice_customers:
            customer.owner_id = alice.id
        
        for customer in bob_customers:
            customer.owner_id = bob.id


        # Types per user
        alice_types = [
            Type(name="Office", owner_id=alice.id),
            Type(name="Electronics", owner_id=alice.id),
            Type(name="Furniture", owner_id=alice.id),
            Type(name="Services", owner_id=alice.id)
        ]
        
        bob_types = [
            Type(name="Services", owner_id=bob.id),
            Type(name="Misc", owner_id=bob.id),
            Type(name="Hardware", owner_id=bob.id),
            Type(name="Software", owner_id=bob.id)
        ]
        
        all_types = alice_types + bob_types
        db.add_all(all_types)
        db.flush()

        today = date.today()

        # Purchases
        purchases = [
            Purchase(
                date=today - timedelta(days=10),
                type_id=alice_types[0].id,
                supplier_id=suppliers[0].id,
                item_name="Printer Paper",
                items_count=10,
                unit_price=Decimal("15.50"),
                total_price=Decimal("155.00"),
                image_url=None,
                notes="Bulk order",
                owner_id=alice.id,
            ),
            Purchase(
                date=today - timedelta(days=5),
                type_id=bob_types[0].id,
                supplier_id=suppliers[1].id,
                item_name="Consulting",
                items_count=2,
                unit_price=Decimal("500.00"),
                total_price=Decimal("1000.00"),
                image_url="https://example.com/invoice1.jpg",
                notes="Retainer",
                owner_id=bob.id,
            ),
            Purchase(
                date=today - timedelta(days=8),
                type_id=alice_types[1].id,
                supplier_id=suppliers[2].id,
                item_name="Laptop Computers",
                items_count=3,
                unit_price=Decimal("899.99"),
                total_price=Decimal("2699.97"),
                image_url="https://example.com/invoice2.jpg",
                notes="New team members",
                owner_id=alice.id,
            )
        ]
        db.add_all(purchases)

        # Create 30 sales records
        sales = []
        item_names = ["Monitors", "Accessories", "Software License", "Office Supplies", "Furniture", 
                     "Electronics", "Services", "Hardware", "Peripherals", "Networking Equipment"]
        
        # Generate sales for Alice (15 sales)
        for i in range(15):
            customer = alice_customers[i % len(alice_customers)]
            type_obj = alice_types[i % len(alice_types)]
            item_name = item_names[i % len(item_names)]
            items_count = (i % 10) + 1
            unit_price = Decimal(str(25.0 + (i % 200) * 5))
            total_price = unit_price * items_count
            image_url = None
            
            sale = Sale(
                date=today - timedelta(days=30 - i),
                type_id=type_obj.id,
                customer_id=customer.id,
                item_name=f"{item_name} #{i+1}",
                items_count=items_count,
                unit_price=unit_price,
                total_price=total_price,
                image_url=image_url,
                notes=f"Order #{i+1} for {customer.name}",
                owner_id=alice.id,
            )
            sales.append(sale)
        
        # Generate sales for Bob (15 sales)
        for i in range(15):
            customer = bob_customers[i % len(bob_customers)]
            type_obj = bob_types[i % len(bob_types)]
            item_name = item_names[(i + 5) % len(item_names)]
            items_count = (i % 8) + 2
            unit_price = Decimal(str(50.0 + (i % 150) * 7))
            total_price = unit_price * items_count
            image_url = None
            
            sale = Sale(
                date=today - timedelta(days=28 - i),
                type_id=type_obj.id,
                customer_id=customer.id,
                item_name=f"{item_name} #{i+1}",
                items_count=items_count,
                unit_price=unit_price,
                total_price=total_price,
                image_url=image_url,
                notes=f"Order #{i+16} for {customer.name}",
                owner_id=bob.id,
            )
            sales.append(sale)
        
        db.add_all(sales)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Manage Financial Manager database")
    parser.add_argument(
        '--action', 
        choices=['reset', 'reset_and_seed'], 
        default='reset_and_seed',
        help='Action to perform: reset (only reset database) or reset_and_seed (reset and insert sample data)'
    )
    
    args = parser.parse_args()
    
    # Always reset the database first
    reset_sqlite_db()
    print("Database reset completed.")
    
    # Insert sample data only if requested
    if args.action == 'reset_and_seed':
        seed_sample_data()
        print("Sample data inserted successfully.")


if __name__ == "__main__":
    main()
