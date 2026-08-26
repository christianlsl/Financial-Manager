"""Write MCP tools backed by the Financial Manager REST API.

All create/update payloads are validated by the backend (amount consistency,
ownership, foreign-key checks), so errors surface with clear messages.
"""

from __future__ import annotations

import json
from datetime import date as date_type
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from mcp.server.fastmcp import Context

from ..api_client import get_client as _get_client
from ..api_client import session_key


def _client(ctx: Context):
    """Backend client bound to the current user's session."""
    return _get_client(session_key(ctx))


def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, default=str)


def _compute_total(count: int, unit_price: float | Decimal) -> str:
    """Compute total_price = count * unit_price rounded to 2 decimals.

    Matches the backend's own price invariant (ROUND_HALF_UP to 2 dp).
    """
    total = Decimal(str(count)) * Decimal(str(unit_price))
    return str(total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _payload(params: dict, *keys: str) -> dict:
    return {k: params[k] for k in keys if params.get(k) is not None}


# ----------------------------------------------------------------------
# Sales
# ----------------------------------------------------------------------
def create_sale(
    date: date_type,
    item_name: str,
    items_count: int,
    unit_price: float,
    type_id: int | None = None,
    customer_id: int | None = None,
    status: str = "draft",
    notes: str | None = None,
    ctx: Context = None,
) -> str:
    """创建一条销售记录（相当于开一张销售单据）。

    金额由系统自动计算为 数量×单价，无需手动传 total_price。
    需要先通过 list_types / list_customers 查到 type_id / customer_id。

    Args:
        date: 销售日期 YYYY-MM-DD。
        item_name: 物料/商品名称。
        items_count: 数量。
        unit_price: 单价（元）。
        type_id: 业务类型 ID（可先查询 list_types）。
        customer_id: 客户 ID（可先查询 list_customers）。
        status: 状态，draft=草稿 / sent=已发送 / paid=已回款，默认 draft。
        notes: 备注。
    """
    body = {
        "date": date.isoformat(),
        "item_name": item_name,
        "items_count": items_count,
        "unit_price": unit_price,
        "total_price": _compute_total(items_count, unit_price),
    }
    body.update(
        _payload(
            dict(
                type_id=type_id,
                customer_id=customer_id,
                status=status,
                notes=notes,
            ),
            "type_id",
            "customer_id",
            "status",
            "notes",
        )
    )
    data = _client(ctx).post("/sales/", json=body)
    return _json(data)


def update_sale(
    sale_id: int,
    date: date_type | None = None,
    item_name: str | None = None,
    items_count: int | None = None,
    unit_price: float | None = None,
    type_id: int | None = None,
    customer_id: int | None = None,
    status: str | None = None,
    notes: str | None = None,
    ctx: Context = None,
) -> str:
    """更新销售记录（只更新传入的字段）。

    若同时修改了数量或单价，总金额会按 数量×单价 自动重新计算。

    Args:
        sale_id: 销售记录 ID。
        date: 销售日期 YYYY-MM-DD。
        item_name: 物料/商品名称。
        items_count: 数量。
        unit_price: 单价（元）。
        type_id: 业务类型 ID。
        customer_id: 客户 ID。
        status: 状态，draft / sent / paid。
        notes: 备注。
    """
    body: dict[str, Any] = {}
    for key, value in (
        ("date", date.isoformat() if date else None),
        ("item_name", item_name),
        ("items_count", items_count),
        ("unit_price", unit_price),
        ("type_id", type_id),
        ("customer_id", customer_id),
        ("status", status),
        ("notes", notes),
    ):
        if value is not None:
            body[key] = value
    if not body:
        raise ValueError("至少需要提供一个要更新的字段")
    # Keep the price invariant valid: recompute total when qty/price changed.
    if "items_count" in body or "unit_price" in body:
        current = _client(ctx).get(f"/sales/{sale_id}")
        count = body.get("items_count", current.get("items_count") or 0)
        price = body.get("unit_price", current.get("unit_price") or 0)
        body["total_price"] = _compute_total(int(count), float(price))
    data = _client(ctx).put(f"/sales/{sale_id}", json=body)
    return _json(data)


def delete_sale(sale_id: int, ctx: Context = None) -> str:
    """删除一条销售记录（不可恢复，请确认后再操作）。

    Args:
        sale_id: 销售记录 ID。
    """
    data = _client(ctx).delete(f"/sales/{sale_id}")
    return _json(data)


# ----------------------------------------------------------------------
# Purchases
# ----------------------------------------------------------------------
def create_purchase(
    date: date_type,
    item_name: str,
    items_count: int,
    unit_price: float,
    type_id: int | None = None,
    supplier_id: int | None = None,
    status: str = "pending",
    notes: str | None = None,
    ctx: Context = None,
) -> str:
    """创建一条采购记录。

    金额由系统自动计算为 数量×单价。需要先通过 list_suppliers / list_types 查到对应 ID。

    Args:
        date: 采购日期 YYYY-MM-DD。
        item_name: 物料/商品名称。
        items_count: 数量。
        unit_price: 单价（元）。
        type_id: 业务类型 ID。
        supplier_id: 供应商 ID。
        status: 状态，pending=待处理 / ordered=已下单 / received=已收货，默认 pending。
        notes: 备注。
    """
    body = {
        "date": date.isoformat(),
        "item_name": item_name,
        "items_count": items_count,
        "unit_price": unit_price,
        "total_price": _compute_total(items_count, unit_price),
    }
    body.update(
        _payload(
            dict(
                type_id=type_id,
                supplier_id=supplier_id,
                status=status,
                notes=notes,
            ),
            "type_id",
            "supplier_id",
            "status",
            "notes",
        )
    )
    data = _client(ctx).post("/purchases/", json=body)
    return _json(data)


def update_purchase(
    purchase_id: int,
    date: date_type | None = None,
    item_name: str | None = None,
    items_count: int | None = None,
    unit_price: float | None = None,
    type_id: int | None = None,
    supplier_id: int | None = None,
    status: str | None = None,
    notes: str | None = None,
    ctx: Context = None,
) -> str:
    """更新采购记录（只更新传入的字段），数量/单价变化时自动重算金额。

    Args:
        purchase_id: 采购记录 ID。
        date: 采购日期 YYYY-MM-DD。
        item_name: 物料/商品名称。
        items_count: 数量。
        unit_price: 单价（元）。
        type_id: 业务类型 ID。
        supplier_id: 供应商 ID。
        status: 状态，pending / ordered / received。
        notes: 备注。
    """
    body: dict[str, Any] = {}
    for key, value in (
        ("date", date.isoformat() if date else None),
        ("item_name", item_name),
        ("items_count", items_count),
        ("unit_price", unit_price),
        ("type_id", type_id),
        ("supplier_id", supplier_id),
        ("status", status),
        ("notes", notes),
    ):
        if value is not None:
            body[key] = value
    if not body:
        raise ValueError("至少需要提供一个要更新的字段")
    if "items_count" in body or "unit_price" in body:
        current = _client(ctx).get(f"/purchases/{purchase_id}")
        count = body.get("items_count", current.get("items_count") or 0)
        price = body.get("unit_price", current.get("unit_price") or 0)
        body["total_price"] = _compute_total(int(count), float(price))
    data = _client(ctx).put(f"/purchases/{purchase_id}", json=body)
    return _json(data)


def delete_purchase(purchase_id: int, ctx: Context = None) -> str:
    """删除一条采购记录（不可恢复，请确认后再操作）。

    Args:
        purchase_id: 采购记录 ID。
    """
    data = _client(ctx).delete(f"/purchases/{purchase_id}")
    return _json(data)


# ----------------------------------------------------------------------
# Customers / Suppliers / Companies / Departments / Types
# ----------------------------------------------------------------------
def create_customer(
    name: str,
    company_id: int = 0,
    phone_number: str | None = None,
    email: str | None = None,
    position: str | None = None,
    department_id: int | None = None,
    ctx: Context = None,
) -> str:
    """创建客户。

    Args:
        name: 客户姓名。
        company_id: 所属公司 ID，0 表示个人客户（默认 0）。
        phone_number: 电话。
        email: 邮箱。
        position: 职位。
        department_id: 部门 ID（可选）。
    """
    body: dict[str, Any] = {"name": name, "company_id": company_id}
    body.update(
        _payload(
            dict(
                phone_number=phone_number,
                email=email,
                position=position,
                department_id=department_id,
            ),
            "phone_number",
            "email",
            "position",
            "department_id",
        )
    )
    data = _client(ctx).post("/customers/", json=body)
    return _json(data)


def create_supplier(
    name: str,
    phone_number: str | None = None,
    email: str | None = None,
    address: str | None = None,
    ctx: Context = None,
) -> str:
    """创建供应商。

    Args:
        name: 供应商名称。
        phone_number: 电话。
        email: 邮箱。
        address: 地址。
    """
    body: dict[str, Any] = {"name": name}
    body.update(
        _payload(
            dict(phone_number=phone_number, email=email, address=address),
            "phone_number",
            "email",
            "address",
        )
    )
    data = _client(ctx).post("/suppliers/", json=body)
    return _json(data)


def create_company(
    name: str,
    address: str | None = None,
    legal_person: str | None = None,
    phone: str | None = None,
    email: str | None = None,
    ctx: Context = None,
) -> str:
    """创建公司（客户所属公司），创建后自动关联当前账号。

    Args:
        name: 公司名称。
        address: 地址。
        legal_person: 法人代表。
        phone: 电话。
        email: 邮箱。
    """
    body: dict[str, Any] = {"name": name}
    body.update(
        _payload(
            dict(address=address, legal_person=legal_person, phone=phone, email=email),
            "address",
            "legal_person",
            "phone",
            "email",
        )
    )
    data = _client(ctx).post("/companies/", json=body)
    return _json(data)


def create_department(name: str, company_id: int, ctx: Context = None) -> str:
    """创建部门（需指定所属公司）。

    Args:
        name: 部门名称。
        company_id: 所属公司 ID。
    """
    data = _client(ctx).post("/departments/", json={"name": name, "company_id": company_id})
    return _json(data)


def create_type(name: str, ctx: Context = None) -> str:
    """创建业务类型（物料分类）。

    Args:
        name: 类型名称。
    """
    data = _client(ctx).post("/types/", json={"name": name})
    return _json(data)


__all__ = [
    "create_sale",
    "update_sale",
    "delete_sale",
    "create_purchase",
    "update_purchase",
    "delete_purchase",
    "create_customer",
    "create_supplier",
    "create_company",
    "create_department",
    "create_type",
]
