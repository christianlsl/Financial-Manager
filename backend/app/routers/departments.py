from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from ..models.company import Company
from ..models.customer import Customer
from ..models.department import Department
from ..models.user import User
from ..schemas.department import DepartmentCreate, DepartmentRead, DepartmentUpdate

router = APIRouter()


def _get_accessible_company(db: Session, current_user: User, company_id: int) -> Company | None:
    if company_id is None:
        return None
    return (
        db.query(Company)
        .filter(Company.id == company_id, Company.vendors.any(User.id == current_user.id))
        .first()
    )


def _get_accessible_department(db: Session, current_user: User, dept_id: int) -> Department | None:
    if dept_id is None:
        return None
    return (
        db.query(Department)
        .join(Company)
        .filter(Department.id == dept_id, Company.vendors.any(User.id == current_user.id))
        .first()
    )


# Leader validation removed: departments no longer have a designated leader.


@router.get("/", response_model=list[DepartmentRead])
def list_departments(
    skip: int = 0,
    limit: int = 200,
    company_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Department).join(Company).filter(Company.vendors.any(User.id == current_user.id))
    if company_id is not None:
        query = query.filter(Department.company_id == company_id)
    departments = (
        query.order_by(Department.company_id.asc(), Department.name.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [DepartmentRead.model_validate(dept) for dept in departments]


@router.post("/", response_model=DepartmentRead)
def create_department(
    data: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = _get_accessible_company(db, current_user, data.company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    department = Department(name=data.name, company_id=company.id)

    db.add(department)
    db.commit()
    db.refresh(department)
    return DepartmentRead.model_validate(department)


@router.put("/{department_id}", response_model=DepartmentRead)
def update_department(
    department_id: int,
    data: DepartmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    department = _get_accessible_department(db, current_user, department_id)
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    payload = data.model_dump(exclude_unset=True)

    if "company_id" in payload:
        new_company_id = payload["company_id"]
        if new_company_id is None:
            raise HTTPException(status_code=400, detail="company_id cannot be null")
        company = _get_accessible_company(db, current_user, new_company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        department.company_id = company.id
    else:
        company = department.company


    if "name" in payload and payload["name"]:
        department.name = payload["name"]

    # partner companies linkage removed

    db.add(department)
    db.commit()
    db.refresh(department)
    return DepartmentRead.model_validate(department)


@router.delete("/{department_id}")
def delete_department(
    department_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    department = _get_accessible_department(db, current_user, department_id)
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    has_members = db.query(Customer.id).filter(Customer.department_id == department_id).first()
    if has_members:
        raise HTTPException(status_code=400, detail="Department has linked customers")
    db.delete(department)
    db.commit()
    return {"ok": True}
