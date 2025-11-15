from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from ..models.company import Company
from ..models.type import Type
from ..models.customer import Customer
from ..models.purchase import Purchase, PurchaseStatusEnum
from ..models.user import User
from ..schemas.purchase import PurchaseCreate, PurchaseList, PurchaseRead, PurchaseUpdate

router = APIRouter()

_CENTS = Decimal("0.01")


def _to_decimal(value: Decimal | float | int | str | None) -> Decimal:
    if value is None:
        raise HTTPException(status_code=400, detail="Amount is required")
    if isinstance(value, Decimal):
        return value.quantize(_CENTS, rounding=ROUND_HALF_UP)
    try:
        return Decimal(str(value)).quantize(_CENTS, rounding=ROUND_HALF_UP)
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=400, detail="Invalid numeric value") from exc


def _expected_total(count: int, unit_price: Decimal) -> Decimal:
    return (Decimal(count) * unit_price).quantize(_CENTS, rounding=ROUND_HALF_UP)


def _apply_price_validation(payload: dict, current_purchase: Purchase | None = None) -> dict:
    if current_purchase is None:
        count = payload.get("items_count")
        unit_price = payload.get("unit_price")
        total_price = payload.get("total_price")
    else:
        if not any(field in payload for field in ("items_count", "unit_price", "total_price")):
            return payload
        count = payload.get("items_count", current_purchase.items_count)
        unit_price = payload.get("unit_price", current_purchase.unit_price)
        total_price = payload.get("total_price")

    if count is None or unit_price is None:
        raise HTTPException(status_code=400, detail="items_count and unit_price are required")

    normalized_unit_price = _to_decimal(unit_price)
    normalized_count = int(count)
    expected_total = _expected_total(normalized_count, normalized_unit_price)
    if total_price is not None:
        provided_total = _to_decimal(total_price)
        if provided_total != expected_total:
            raise HTTPException(status_code=400, detail="total_price must equal items_count * unit_price")
    payload["items_count"] = normalized_count
    payload["unit_price"] = normalized_unit_price
    payload["total_price"] = expected_total
    return payload


def _customer_access_filter(current_user: User):
    return Customer.vendors.any(User.id == current_user.id)


def _get_accessible_customer(db: Session, current_user: User, customer_id: int) -> Customer | None:
    return (
        db.query(Customer).filter(Customer.id == customer_id, _customer_access_filter(current_user)).first()
    )


@router.get("/", response_model=PurchaseList)
def list_purchases(
    skip: int = 0,
    limit: int = 100,
    type_id: int | None = None,
    customer_id: int | None = None,
    company_id: int | None = None,
    status: str | None = None,
    search: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    amount_min: Decimal | None = None,
    amount_max: Decimal | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List purchases with advanced filtering similar to sales."""
    query = db.query(Purchase).filter(Purchase.owner_id == current_user.id)
    joined_customer = False
    joined_company = False

    def ensure_customer_join():
        nonlocal query, joined_customer
        if not joined_customer:
            query = query.join(Customer)
            joined_customer = True

    def ensure_company_join():
        nonlocal query, joined_company
        ensure_customer_join()
        if not joined_company:
            query = query.outerjoin(Company, Customer.company_id == Company.id)
            joined_company = True

    if status:
        normalized_status = status.strip().lower()
        if normalized_status not in {
            PurchaseStatusEnum.PENDING,
            PurchaseStatusEnum.ORDERED,
            PurchaseStatusEnum.RECEIVED,
        }:
            raise HTTPException(status_code=400, detail="Invalid status filter")
        query = query.filter(Purchase.status == normalized_status)
    if type_id is not None:
        query = query.filter(Purchase.type_id == type_id)
    if customer_id is not None:
        query = query.filter(Purchase.customer_id == customer_id)
    if company_id is not None:
        ensure_customer_join()
        query = query.filter(Customer.company_id == company_id)
    if search and search.strip():
        ensure_company_join()
        keyword = f"%{search.strip().lower()}%"
        query = query.filter(
            or_(
                func.lower(func.coalesce(Purchase.item_name, "")).like(keyword),
                func.lower(func.coalesce(Customer.name, "")).like(keyword),
                func.lower(func.coalesce(Company.name, "")).like(keyword),
            )
        )
    if date_from is not None:
        query = query.filter(Purchase.date >= date_from)
    if date_to is not None:
        query = query.filter(Purchase.date <= date_to)

    def _to_decimal_local(val: Decimal | float | int | str | None) -> Decimal:
        if val is None:
            raise HTTPException(status_code=400, detail="Amount is required")
        if isinstance(val, Decimal):
            return val.quantize(_CENTS, rounding=ROUND_HALF_UP)
        try:
            return Decimal(str(val)).quantize(_CENTS, rounding=ROUND_HALF_UP)
        except Exception as exc:  # pragma: no cover - defensive
            raise HTTPException(status_code=400, detail="Invalid numeric value") from exc

    normalized_amount_min = _to_decimal_local(amount_min) if amount_min is not None else None
    normalized_amount_max = _to_decimal_local(amount_max) if amount_max is not None else None
    if (
        normalized_amount_min is not None
        and normalized_amount_max is not None
        and normalized_amount_min > normalized_amount_max
    ):
        raise HTTPException(status_code=400, detail="amount_min cannot be greater than amount_max")
    if normalized_amount_min is not None:
        query = query.filter(Purchase.total_price >= normalized_amount_min)
    if normalized_amount_max is not None:
        query = query.filter(Purchase.total_price <= normalized_amount_max)

    total = query.count()
    items = query.order_by(Purchase.date.desc(), Purchase.id.desc()).offset(skip).limit(limit).all()
    return PurchaseList(items=items, total=total)


@router.post("/", response_model=PurchaseRead)
def create_purchase(
    data: PurchaseCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    if data.type_id is not None:
        type_obj = db.query(Type).filter(Type.id == data.type_id, Type.owner_id == current_user.id).first()
        if not type_obj:
            raise HTTPException(status_code=404, detail="Type not found")
    payload = _apply_price_validation(data.model_dump())
    if payload.get("customer_id") is None:
        raise HTTPException(status_code=400, detail="Customer is required")
    customer_obj = _get_accessible_customer(db, current_user, payload["customer_id"])
    if not customer_obj:
        raise HTTPException(status_code=404, detail="Customer not found")
    purchase = Purchase(**payload, owner_id=current_user.id)
    db.add(purchase)
    db.commit()
    db.refresh(purchase)
    return purchase


@router.get("/{purchase_id}", response_model=PurchaseRead)
def get_purchase(
    purchase_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    purchase = (
        db.query(Purchase).filter(Purchase.id == purchase_id, Purchase.owner_id == current_user.id).first()
    )
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    return purchase


@router.put("/{purchase_id}", response_model=PurchaseRead)
def update_purchase(
    purchase_id: int,
    data: PurchaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    purchase = (
        db.query(Purchase).filter(Purchase.id == purchase_id, Purchase.owner_id == current_user.id).first()
    )
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    update_payload = data.model_dump(exclude_unset=True)
    if "type_id" in update_payload:
        new_type_id = update_payload["type_id"]
        if new_type_id is not None:
            type_obj = db.query(Type).filter(Type.id == new_type_id, Type.owner_id == current_user.id).first()
            if not type_obj:
                raise HTTPException(status_code=404, detail="Type not found")
    if "customer_id" in update_payload:
        new_customer_id = update_payload["customer_id"]
        if new_customer_id is None:
            raise HTTPException(status_code=400, detail="Customer is required")
        customer_obj = _get_accessible_customer(db, current_user, new_customer_id)
        if not customer_obj:
            raise HTTPException(status_code=404, detail="Customer not found")
    update_payload = _apply_price_validation(update_payload, current_purchase=purchase)
    for k, v in update_payload.items():
        setattr(purchase, k, v)
    db.add(purchase)
    db.commit()
    db.refresh(purchase)
    return purchase


@router.delete("/{purchase_id}")
def delete_purchase(
    purchase_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    purchase = (
        db.query(Purchase).filter(Purchase.id == purchase_id, Purchase.owner_id == current_user.id).first()
    )
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    db.delete(purchase)
    db.commit()
    return {"ok": True}
