from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, case, or_, select
from sqlalchemy.orm import Session, joinedload

from ..db import get_db
from ..deps import get_current_user
from ..models.company import Company
from ..models.customer import Customer
from ..models.sale import Sale
from ..models.department import Department
from ..models.user import User

from ..schemas.customer import CustomerCreate, CustomerGroup, CustomerRead, CustomerUpdate
from ..models.user_company import user_company_table

router = APIRouter()


def _customer_access_filter(current_user: User):
    return Customer.vendors.any(User.id == current_user.id)


def _get_accessible_department(db: Session, current_user: User, department_id: int) -> Department | None:
    return (
        db.query(Department)
        .join(Company)
        .filter(Department.id == department_id, Company.vendors.any(User.id == current_user.id))
        .first()
    )


@router.get("/", response_model=list[CustomerGroup])
def list_customers(
    skip: int = 0,
    limit: int = 100,
    company_id: int | None = None,
    department_id: int | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    access_filter = _customer_access_filter(current_user)
    query = (
        db.query(Customer)
        .options(joinedload(Customer.company), joinedload(Customer.department))
        .filter(access_filter)
    )
    if company_id is not None:
        query = query.filter(Customer.company_id == company_id)
    if department_id is not None:
        query = query.filter(Customer.department_id == department_id)
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Customer.name.ilike(like),
                Customer.phone_number.ilike(like),
                Customer.email.ilike(like),
                Customer.position.ilike(like),
            )
        )
    order_expr = case((Customer.company_id == 0, 0), else_=1)
    customers = query.order_by(order_expr, Customer.company_id, Customer.id).offset(skip).limit(limit).all()
    groups: dict[int, list[Customer]] = {}
    order: list[int] = []
    for item in customers:
        key = item.company_id
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(item)
    return [
        CustomerGroup(
            company_id=company_key,
            customers=[CustomerRead.model_validate(entry) for entry in groups[company_key]],
        )
        for company_key in order
    ]


@router.get("/count", response_model=int)
def count_customers(
    company_id: int | None = None,
    department_id: int | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    access_filter = _customer_access_filter(current_user)
    query = db.query(Customer).filter(access_filter)
    if company_id is not None:
        query = query.filter(Customer.company_id == company_id)
    if department_id is not None:
        query = query.filter(Customer.department_id == department_id)
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Customer.name.ilike(like),
                Customer.phone_number.ilike(like),
                Customer.email.ilike(like),
                Customer.position.ilike(like),
            )
        )
    return query.count()


@router.post("/", response_model=CustomerRead)
def create_customer(
    data: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    payload = data.model_dump()
    company_id = payload.get("company_id", 0)
    if company_id < 0:
        raise HTTPException(status_code=400, detail="Invalid company id")
    if company_id != 0:
        company = (
            db.query(Company)
            .filter(Company.id == company_id, Company.vendors.any(User.id == current_user.id))
            .first()
        )
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

    department_id = payload.get("department_id")
    if department_id is not None:
        department_obj = _get_accessible_department(db, current_user, department_id)
        if not department_obj:
            raise HTTPException(status_code=404, detail="Department not found")

    existing = (
        db.query(Customer)
        .filter(
            Customer.name == payload.get("name"),
            Customer.company_id == company_id,
            Customer.department_id == department_id,
            _customer_access_filter(current_user),
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Customer already exists")

    customer = Customer(**payload)
    customer.vendors.append(current_user)
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("/{customer_id}", response_model=CustomerRead)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    access_filter = _customer_access_filter(current_user)
    customer = db.query(Customer).filter(Customer.id == customer_id, access_filter).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    if customer.company_id > 0:
        link_exists = db.execute(
            select(user_company_table.c.company_id).where(
                and_(
                    user_company_table.c.user_id == current_user.id,
                    user_company_table.c.company_id == customer.company_id,
                )
            )
        ).first()
        if not link_exists:
            raise HTTPException(status_code=403, detail="Customer not accessible")
    return customer


@router.put("/{customer_id}", response_model=CustomerRead)
def update_customer(
    customer_id: int,
    data: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    access_filter = _customer_access_filter(current_user)
    customer = db.query(Customer).filter(Customer.id == customer_id, access_filter).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    payload = data.model_dump(exclude_unset=True)
    if "company_id" in payload:
        new_company_id = payload["company_id"]
        if new_company_id is None:
            new_company_id = 0
        if new_company_id < 0:
            raise HTTPException(status_code=400, detail="Invalid company id")
        if new_company_id == 0:
            payload["company_id"] = 0
            if current_user not in customer.vendors:
                customer.vendors.append(current_user)
        else:
            company = (
                db.query(Company)
                .filter(Company.id == new_company_id, Company.vendors.any(User.id == current_user.id))
                .first()
            )
            if not company:
                raise HTTPException(status_code=404, detail="Company not found")

    if "department_id" in payload:
        new_department_id = payload["department_id"]
        if new_department_id is not None:
            department_obj = _get_accessible_department(db, current_user, new_department_id)
            if not department_obj:
                raise HTTPException(status_code=404, detail="Department not found")

    for key, value in payload.items():
        setattr(customer, key, value)

    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.delete("/{customer_id}")
def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    access_filter = _customer_access_filter(current_user)
    customer = db.query(Customer).filter(Customer.id == customer_id, access_filter).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    has_sales = db.query(Sale.id).filter(Sale.customer_id == customer_id).first()
    if has_sales:
        raise HTTPException(status_code=400, detail="Customer has linked sales")

    db.delete(customer)
    db.commit()
    return {"ok": True}
