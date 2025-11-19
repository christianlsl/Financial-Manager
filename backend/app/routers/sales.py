from datetime import date
from decimal import Decimal, ROUND_HALF_UP
import json
import logging
from typing import Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from pydantic import ValidationError
from starlette.datastructures import UploadFile as StarletteUploadFile

from ..db import get_db
from ..deps import get_current_user
from ..models.company import Company
from ..models.customer import Customer
from ..models.sale import Sale, SaleStatusEnum
from ..models.type import Type
from ..models.user import User
from ..schemas.sale import SaleCreate, SaleImageUploadResponse, SaleList, SaleRead, SaleUpdate
from ..services.image_uploader import ImageUploadError, uploader

logger = logging.getLogger(__name__)

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


def _apply_price_validation(payload: dict, current_sale: Sale | None = None) -> dict:
    """Ensure unit price exists and total equals count * unit price."""
    if current_sale is None:
        count = payload.get("items_count")
        unit_price = payload.get("unit_price")
        total_price = payload.get("total_price")
    else:
        if not any(field in payload for field in ("items_count", "unit_price", "total_price")):
            return payload
        count = payload.get("items_count", current_sale.items_count)
        unit_price = payload.get("unit_price", current_sale.unit_price)
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


async def _parse_sale_update_request(request: Request) -> tuple[dict[str, Any], UploadFile | None]:
    content_type = request.headers.get("content-type", "").lower()
    if "multipart/form-data" in content_type:
        form_data = await request.form()
        payload: dict[str, Any] = {}
        image_file: UploadFile | None = None
        for candidate_key in ("image_file", "file", "image"):
            candidate = form_data.get(candidate_key)
            if isinstance(candidate, StarletteUploadFile):
                image_file = candidate
                break
        for key, value in form_data.multi_items():
            if key in {"image_file", "file", "image"} and isinstance(value, StarletteUploadFile):
                continue
            if key == "data" and isinstance(value, str):
                stripped = value.strip()
                if not stripped:
                    continue
                try:
                    decoded = json.loads(stripped)
                except json.JSONDecodeError as exc:  # pragma: no cover - invalid payload
                    raise HTTPException(status_code=400, detail="Invalid data payload") from exc
                if not isinstance(decoded, dict):
                    raise HTTPException(status_code=400, detail="Invalid data payload")
                payload.update(decoded)
                continue
            if isinstance(value, str) and value == "":
                continue
            payload[key] = value
        return payload, image_file

    body = await request.body()
    if not body:
        return {}, None
    try:
        decoded_body = json.loads(body)
    except json.JSONDecodeError as exc:  # pragma: no cover - invalid json
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc
    if not isinstance(decoded_body, dict):
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    return decoded_body, None


def _normalize_update_payload_types(payload: dict[str, Any]) -> dict[str, Any]:
    """Coerce common fields from strings to their target types for update requests.

    - date: str -> date
    - items_count, customer_id, type_id: str -> int
    - unit_price, total_price: str -> Decimal (handled later by _to_decimal)
    - empty strings -> None for optional text fields
    """
    if not payload:
        return payload
    normalized = dict(payload)
    # Normalize date
    d = normalized.get("date")
    if isinstance(d, str) and d.strip():
        try:
            normalized["date"] = date.fromisoformat(d.strip())
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid date format, expected YYYY-MM-DD") from exc
    # Normalize integer-like fields
    for k in ("items_count", "customer_id", "type_id"):
        v = normalized.get(k)
        if isinstance(v, str) and v.strip():
            try:
                normalized[k] = int(v)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=f"Invalid integer value for {k}") from exc
    # Normalize decimals as strings (Decimal parsing happens in _apply_price_validation)
    for k in ("unit_price", "total_price"):
        v = normalized.get(k)
        if isinstance(v, (int, float)):
            continue
        if isinstance(v, str):
            s = v.strip()
            if s == "":
                normalized[k] = None
            else:
                normalized[k] = s
    # Empty strings to None for optional text fields
    for k in ("item_name", "notes", "status"):
        v = normalized.get(k)
        if isinstance(v, str) and v.strip() == "":
            normalized[k] = None
    return normalized


@router.get("/", response_model=SaleList)
def list_sales(
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
    query = db.query(Sale).filter(Sale.owner_id == current_user.id)
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
        if normalized_status not in {SaleStatusEnum.DRAFT, SaleStatusEnum.SENT, SaleStatusEnum.PAID}:
            raise HTTPException(status_code=400, detail="Invalid status filter")
        query = query.filter(Sale.status == normalized_status)
    if type_id is not None:
        query = query.filter(Sale.type_id == type_id)
    if customer_id is not None:
        query = query.filter(Sale.customer_id == customer_id)
    if company_id is not None:
        ensure_customer_join()
        query = query.filter(Customer.company_id == company_id)
    if search and search.strip():
        ensure_company_join()
        keyword = f"%{search.strip().lower()}%"
        query = query.filter(
            or_(
                func.lower(func.coalesce(Sale.item_name, "")).like(keyword),
                func.lower(func.coalesce(Customer.name, "")).like(keyword),
                func.lower(func.coalesce(Company.name, "")).like(keyword),
            )
        )
    if date_from is not None:
        query = query.filter(Sale.date >= date_from)
    if date_to is not None:
        query = query.filter(Sale.date <= date_to)

    normalized_amount_min = _to_decimal(amount_min) if amount_min is not None else None
    normalized_amount_max = _to_decimal(amount_max) if amount_max is not None else None
    if (
        normalized_amount_min is not None
        and normalized_amount_max is not None
        and normalized_amount_min > normalized_amount_max
    ):
        raise HTTPException(status_code=400, detail="amount_min cannot be greater than amount_max")
    if normalized_amount_min is not None:
        query = query.filter(Sale.total_price >= normalized_amount_min)
    if normalized_amount_max is not None:
        query = query.filter(Sale.total_price <= normalized_amount_max)

    total = query.count()
    items = query.order_by(Sale.date.desc(), Sale.id.desc()).offset(skip).limit(limit).all()
    return SaleList(items=items, total=total)


@router.post("/", response_model=SaleRead)
def create_sale(
    data: SaleCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
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
    sale = Sale(**payload, owner_id=current_user.id)
    db.add(sale)
    db.commit()
    db.refresh(sale)
    return sale


@router.post("/images", response_model=SaleImageUploadResponse)
async def upload_sale_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="仅支持图片格式上传")
    data = await file.read()
    try:
        url = uploader.upload(data, file.filename)
    except ImageUploadError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return SaleImageUploadResponse(url=url)


@router.get("/{sale_id}", response_model=SaleRead)
def get_sale(sale_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sale = db.query(Sale).filter(Sale.id == sale_id, Sale.owner_id == current_user.id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    return sale


@router.put("/{sale_id}", response_model=SaleRead)
async def update_sale(
    sale_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sale = db.query(Sale).filter(Sale.id == sale_id, Sale.owner_id == current_user.id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    payload_data, upload_file = await _parse_sale_update_request(request)
    # Coerce common field types to avoid pydantic validation edge cases on multipart
    payload_data = _normalize_update_payload_types(payload_data)
    try:
        parsed_data = SaleUpdate(**payload_data)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc
    update_payload = parsed_data.model_dump(exclude_unset=True)
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
    new_image_url: str | None = None
    # If client explicitly clears image_url (and no new upload), we should delete the previous image
    remove_image_requested = (
        upload_file is None and "image_url" in update_payload and update_payload.get("image_url") is None
    )
    previous_image_url: str | None = sale.image_url if (upload_file is not None or remove_image_requested) else None
    if upload_file is not None:
        if not upload_file.content_type or not upload_file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="仅支持图片格式上传")
        file_bytes = await upload_file.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="图片内容为空")
        try:
            new_image_url = uploader.upload(file_bytes, upload_file.filename)
        except ImageUploadError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        update_payload["image_url"] = new_image_url

    update_payload = _apply_price_validation(update_payload, current_sale=sale)
    for k, v in update_payload.items():
        setattr(sale, k, v)
    db.add(sale)
    db.commit()
    db.refresh(sale)
    # Best-effort cleanup: delete previous image if replaced or explicitly removed
    if previous_image_url and ((new_image_url and previous_image_url != new_image_url) or remove_image_requested):
        try:
            uploader.delete(previous_image_url)
        except ImageUploadError as exc:  # pragma: no cover - best effort cleanup
            logger.warning("Failed to delete old sale image %s: %s", previous_image_url, exc)
    return sale


@router.delete("/{sale_id}")
def delete_sale(sale_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sale = db.query(Sale).filter(Sale.id == sale_id, Sale.owner_id == current_user.id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    db.delete(sale)
    db.commit()
    return {"ok": True}
