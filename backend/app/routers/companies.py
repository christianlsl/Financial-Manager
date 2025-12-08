from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from ..models.company import Company
from ..models.customer import Customer
from ..models.department import Department
from ..models.supplier import Supplier
from ..models.user import User
from ..schemas.company import CompanyCreate, CompanyRead, CompanyUpdate


router = APIRouter()


@router.get("/", response_model=list[CompanyRead])
def list_customer_companies(skip: int = 0, limit: int = 100, q: str | None = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(Company).filter(Company.vendors.any(User.id == current_user.id))
    if q:
        like = f"%{q}%"
        query = query.filter(Company.name.ilike(like))
    return query.offset(skip).limit(limit).all()


@router.post("/", response_model=CompanyRead)
def create_company(data: CompanyCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    payload = data.model_dump()
    existing = db.query(Company).filter(Company.name == data.name, Company.vendors.any(User.id == current_user.id)).first()
    if existing:
        matches = all(getattr(existing, key) == value for key, value in payload.items())
        if not matches:
            raise HTTPException(status_code=400, detail="公司名称已存在且信息不匹配")
        return existing

    company = Company(**payload)
    company.vendors.append(current_user)
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.get("/{company_id}", response_model=CompanyRead)
def get_company(company_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    company = db.query(Company).filter(Company.id == company_id, Company.vendors.any(User.id == current_user.id)).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.put("/{company_id}", response_model=CompanyRead)
def update_company(company_id: int, data: CompanyUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    company = db.query(Company).filter(Company.id == company_id, Company.vendors.any(User.id == current_user.id)).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(company, k, v)
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.delete("/{company_id}")
def delete_company(company_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    company = db.query(Company).filter(Company.id == company_id, Company.vendors.any(User.id == current_user.id)).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    has_customers = db.query(Customer.id).filter(Customer.company_id == company_id).first()
    if has_customers:
        raise HTTPException(status_code=400, detail="Company has linked contacts")
    has_departments = db.query(Department.id).filter(Department.company_id == company_id).first()
    if has_departments:
        raise HTTPException(status_code=400, detail="Company has linked departments")
    db.delete(company)
    db.commit()
    return {"ok": True}
