from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from ..models.company import Company
from ..models.sale import Sale
from ..models.type import Type
from ..models.user import User
from ..schemas.sale import SaleCreate, SaleRead, SaleUpdate

router = APIRouter()


@router.get("/", response_model=list[SaleRead])
def list_sales(skip: int = 0, limit: int = 100, company_id: int | None = None, type_id: int | None = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(Sale).filter(Sale.owner_id == current_user.id)
    if company_id is not None:
        query = query.filter(Sale.company_id == company_id)
    if type_id is not None:
        query = query.filter(Sale.type_id == type_id)
    return query.offset(skip).limit(limit).all()


@router.post("/", response_model=SaleRead)
def create_sale(data: SaleCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if data.type_id is not None:
        type_obj = db.query(Type).filter(Type.id == data.type_id, Type.owner_id == current_user.id).first()
        if not type_obj:
            raise HTTPException(status_code=404, detail="Type not found")
    if data.company_id is not None:
        company_obj = db.query(Company).filter(Company.id == data.company_id, Company.owners.any(User.id == current_user.id)).first()
        if not company_obj:
            raise HTTPException(status_code=404, detail="Company not found")
    sale = Sale(**data.model_dump(), owner_id=current_user.id)
    db.add(sale)
    db.commit()
    db.refresh(sale)
    return sale


@router.get("/{sale_id}", response_model=SaleRead)
def get_sale(sale_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sale = db.query(Sale).filter(Sale.id == sale_id, Sale.owner_id == current_user.id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    return sale


@router.put("/{sale_id}", response_model=SaleRead)
def update_sale(sale_id: int, data: SaleUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sale = db.query(Sale).filter(Sale.id == sale_id, Sale.owner_id == current_user.id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
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
        setattr(sale, k, v)
    db.add(sale)
    db.commit()
    db.refresh(sale)
    return sale


@router.delete("/{sale_id}")
def delete_sale(sale_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sale = db.query(Sale).filter(Sale.id == sale_id, Sale.owner_id == current_user.id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    db.delete(sale)
    db.commit()
    return {"ok": True}
