from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from ..models.supplier import Supplier
from ..models.purchase import Purchase
from ..models.user import User

from ..schemas.supplier import SupplierCreate, SupplierRead, SupplierUpdate

router = APIRouter()


def _supplier_access_filter(current_user: User):
    return Supplier.customers.any(User.id == current_user.id)


@router.get("/", response_model=list[SupplierRead])
def list_suppliers(
    skip: int = 0,
    limit: int = 100,
    q: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    access_filter = _supplier_access_filter(current_user)
    query = db.query(Supplier).filter(access_filter)
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Supplier.name.ilike(like),
                Supplier.phone_number.ilike(like),
                Supplier.email.ilike(like),
                Supplier.address.ilike(like),
            )
        )
    suppliers = query.order_by(Supplier.id).offset(skip).limit(limit).all()
    return [SupplierRead.model_validate(entry) for entry in suppliers]


@router.get("/count", response_model=int)
def count_suppliers(
    q: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    access_filter = _supplier_access_filter(current_user)
    query = db.query(Supplier).filter(access_filter)
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Supplier.name.ilike(like),
                Supplier.phone_number.ilike(like),
                Supplier.email.ilike(like),
                Supplier.address.ilike(like),
            )
        )
    return query.count()


@router.post("/", response_model=SupplierRead)
def create_supplier(
    data: SupplierCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    access_filter = _supplier_access_filter(current_user)
    payload = data.model_dump()
    existing = db.query(Supplier).filter(Supplier.name == payload.get("name"), access_filter).first()
    if existing:
        raise HTTPException(status_code=409, detail="Supplier already exists")

    payload = data.model_dump()
    supplier = Supplier(**payload)
    supplier.customers.append(current_user)
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.get("/{supplier_id}", response_model=SupplierRead)
def get_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    access_filter = _supplier_access_filter(current_user)
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id, access_filter).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier


@router.put("/{supplier_id}", response_model=SupplierRead)
def update_supplier(
    supplier_id: int,
    data: SupplierUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    access_filter = _supplier_access_filter(current_user)
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id, access_filter).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    payload = data.model_dump(exclude_unset=True)
    for key, value in payload.items():
        setattr(supplier, key, value)

    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.delete("/{supplier_id}")
def delete_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    access_filter = _supplier_access_filter(current_user)
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id, access_filter).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    has_purchases = db.query(Purchase.id).filter(Purchase.supplier_id == supplier_id).first()
    if has_purchases:
        raise HTTPException(status_code=400, detail="Supplier has linked purchases")

    db.delete(supplier)
    db.commit()
    return {"ok": True}
