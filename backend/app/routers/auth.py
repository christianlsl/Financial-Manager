from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from ..models.user import User
from ..schemas.user import UserCreate, UserRead, Token, LoginRequest
from ..core.security import get_password_hash, verify_password, create_access_token

router = APIRouter()


@router.post("/register", response_model=UserRead)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=user_in.email, hashed_password=get_password_hash(user_in.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    access_token = create_access_token(subject=user.email)
    return Token(access_token=access_token)

@router.post("/bind-company")
def bind_company(company_id: int | None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # company_id: set to value to bind, or None to unbind
    from ..models.company import Company

    if company_id is None:
        current_user.company_id = None
        db.add(current_user)
        db.commit()
        db.refresh(current_user)
        return {"ok": True, "company_id": None}

    company = db.query(Company).filter(Company.id == company_id, Company.owners.any(User.id == current_user.id)).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    current_user.company_id = company_id
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return {"ok": True, "company_id": current_user.company_id}
