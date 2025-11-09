from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from ..models.company import Company
from ..models.type import Type
from ..models.purchase import Purchase
from ..models.user import User
from ..schemas.purchase import PurchaseCreate, PurchaseRead, PurchaseUpdate

router = APIRouter()


@router.get("/", response_model=list[PurchaseRead])
def list_purchases(skip: int = 0, limit: int = 100, company_id: int | None = None, type_id: int | None = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(Purchase).filter(Purchase.owner_id == current_user.id)
    if company_id is not None:
        query = query.filter(Purchase.company_id == company_id)
    if type_id is not None:
        query = query.filter(Purchase.type_id == type_id)
    return query.offset(skip).limit(limit).all()


@router.post("/", response_model=PurchaseRead)
def create_purchase(data: PurchaseCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if data.type_id is not None:
        type_obj = db.query(Type).filter(Type.id == data.type_id, Type.owner_id == current_user.id).first()
        if not type_obj:
            raise HTTPException(status_code=404, detail="Type not found")
    if data.company_id is not None:
        company_obj = db.query(Company).filter(Company.id == data.company_id, Company.owners.any(User.id == current_user.id)).first()
        if not company_obj:
            raise HTTPException(status_code=404, detail="Company not found")
    purchase = Purchase(**data.model_dump(), owner_id=current_user.id)
    db.add(purchase)
    db.commit()
    db.refresh(purchase)
    return purchase


@router.get("/{purchase_id}", response_model=PurchaseRead)
def get_purchase(purchase_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    purchase = db.query(Purchase).filter(Purchase.id == purchase_id, Purchase.owner_id == current_user.id).first()
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    return purchase


@router.put("/{purchase_id}", response_model=PurchaseRead)
def update_purchase(purchase_id: int, data: PurchaseUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    purchase = db.query(Purchase).filter(Purchase.id == purchase_id, Purchase.owner_id == current_user.id).first()
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    update_payload = data.model_dump(exclude_unset=True)
    if "type_id" in update_payload:
        new_type_id = update_payload["type_id"]
        if new_type_id is not None:
            type_obj = db.query(Type).filter(Type.id == new_type_id, Type.owner_id == current_user.id).first()
            if not type_obj:
                raise HTTPException(status_code=404, detail="Type not found")
    if "company_id" in update_payload:
        new_company_id = update_payload["company_id"]
        if new_company_id is not None:
            company_obj = db.query(Company).filter(Company.id == new_company_id, Company.owners.any(User.id == current_user.id)).first()
            if not company_obj:
                raise HTTPException(status_code=404, detail="Company not found")
    for k, v in update_payload.items():
        setattr(purchase, k, v)
    db.add(purchase)
    db.commit()
    db.refresh(purchase)
    return purchase


@router.delete("/{purchase_id}")
def delete_purchase(purchase_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    purchase = db.query(Purchase).filter(Purchase.id == purchase_id, Purchase.owner_id == current_user.id).first()
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    db.delete(purchase)
    db.commit()
    return {"ok": True}
