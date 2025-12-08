from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from ..models.type import Type
from ..models.user import User
from ..schemas.type import TypeCreate, TypeRead, TypeUpdate

router = APIRouter()


@router.get("/", response_model=list[TypeRead])
def list_types(skip: int = 0, limit: int = 100, q: str | None = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(Type).filter(Type.owner_id == current_user.id)
    if q:
        like = f"%{q}%"
        query = query.filter(Type.name.ilike(like))
    return query.offset(skip).limit(limit).all()


@router.post("/", response_model=TypeRead, status_code=201)
def create_type(data: TypeCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    existing = db.query(Type).filter(Type.name == data.name, Type.owner_id == current_user.id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Type already exists")

    type_obj = Type(name=data.name, owner_id=current_user.id)
    db.add(type_obj)
    db.commit()
    db.refresh(type_obj)
    return type_obj


@router.get("/{type_id}", response_model=TypeRead)
def get_type(type_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    type_obj = db.query(Type).filter(Type.id == type_id, Type.owner_id == current_user.id).first()
    if not type_obj:
        raise HTTPException(status_code=404, detail="Type not found")
    return type_obj


@router.put("/{type_id}", response_model=TypeRead)
def update_type(type_id: int, data: TypeUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    type_obj = db.query(Type).filter(Type.id == type_id, Type.owner_id == current_user.id).first()
    if not type_obj:
        raise HTTPException(status_code=404, detail="Type not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(type_obj, key, value)
    db.add(type_obj)
    db.commit()
    db.refresh(type_obj)
    return type_obj


@router.delete("/{type_id}")
def delete_type(type_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    type_obj = db.query(Type).filter(Type.id == type_id, Type.owner_id == current_user.id).first()
    if not type_obj:
        raise HTTPException(status_code=404, detail="Type not found")
    db.delete(type_obj)
    db.commit()
    return {"ok": True}
