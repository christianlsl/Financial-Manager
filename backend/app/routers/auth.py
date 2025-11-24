from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from ..models.user import User
from ..schemas.user import (
    UserCreate,
    UserRead,
    Token,
    LoginRequest,
    ChangePasswordRequest,
    UserProfileUpdate,
)
from ..core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    decrypt_password,
    get_public_key_pem,
)

router = APIRouter()


@router.post("/register", response_model=UserRead)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    company_name: str | None = None
    if user_in.company_name is not None:
        company_name = user_in.company_name
        if not company_name:
            raise HTTPException(status_code=400, detail="Company name is required")
    # Decrypt required encrypted password
    try:
        password_plain = decrypt_password(user_in.enc_password)
    except Exception as e:
        # 添加详细的错误日志
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Password decryption failed: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid encrypted password")
    user = User(
        email=user_in.email, hashed_password=get_password_hash(password_plain), company_name=company_name
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.post("/login", response_model=Token)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    # Decrypt required encrypted password
    try:
        password_plain = decrypt_password(data.enc_password)
    except Exception:
        # treat as invalid credentials rather than leaking decryption errors
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    if not user or not verify_password(password_plain, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    access_token = create_access_token(subject=user.email)
    return Token(access_token=access_token)


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return current_user


@router.post("/change-password")
def change_password(
    data: ChangePasswordRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    # Decrypt required encrypted fields
    try:
        cur_plain = decrypt_password(data.enc_current_password)
        new_plain = decrypt_password(data.enc_new_password)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid encrypted password")
    if not verify_password(cur_plain, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    current_user.hashed_password = get_password_hash(new_plain)
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return {"ok": True}


@router.get("/pubkey")
def get_pubkey():
    return {"alg": "RSA-PKCS1v15", "pem": get_public_key_pem()}


@router.put("/update-profile")
def update_profile(
    data: UserProfileUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    payload = data.model_dump(exclude_unset=True)
    if "email" in payload and payload["email"] != current_user.email:
        exists = db.query(User).filter(User.email == payload["email"]).first()
        if exists:
            raise HTTPException(status_code=400, detail="Email already registered")
        current_user.email = payload["email"]
    if "company_name" in payload:
        current_user.company = payload["company_name"]
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return {"ok": True}
