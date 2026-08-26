"""Read-only MCP tools backed by the Financial Manager REST API.

Every tool operates as the user who logged in via the `login` tool
(per-session identity). Results are JSON strings so the AI assistant
can parse them directly.
"""

from __future__ import annotations

import json
from datetime import date as date_type
from typing import Any

from mcp.server.fastmcp import Context

from ..api_client import get_client as _get_client
from ..api_client import session_key


def _client(ctx: Context):
    """Backend client bound to the current user's session."""
    return _get_client(session_key(ctx))


def _json(data: Any) -> str:
    """Serialise API payloads that may contain Decimal / date values."""
    return json.dumps(data, ensure_ascii=False, default=str)


def _opt(params: dict, *keys: str) -> dict:
    """Drop None values for the given keys so we never send null filters."""
    return {k: params[k] for k in keys if params.get(k) is not None}


# ----------------------------------------------------------------------
# Statistics
# ----------------------------------------------------------------------
def get_summary(ctx: Context) -> str:
    """获取财务概览：当月/年度采购总额、销售总额、利润（快速了解经营状况）。"""
    data = _client(ctx).get("/statistics/summary")
    return _json(data)


def get_statistics(
    analysis_type: str = "monthly",
    date_from: date_type | None = None,
    date_to: date_type | None = None,
    ctx: Context = None,
) -> str:
    """获取详细财务统计报表（趋势、同比环比、利润、Top客户）。

    Args:
        analysis_type: 分析粒度，可选 yearly / monthly / daily，默认 monthly。
        date_from: 起始日期，格式 YYYY-MM-DD，缺省为最近一段时间。
        date_to: 结束日期，格式 YYYY-MM-DD。
    """
    params = {"analysis_type": analysis_type}
    if date_from:
        params["date_from"] = date_from.isoformat()
    if date_to:
        params["date_to"] = date_to.isoformat()
    data = _client(ctx).get("/statistics/", params=params)
    return _json(data)


# ----------------------------------------------------------------------
# Sales
# ----------------------------------------------------------------------
def list_sales(
    skip: int = 0,
    limit: int = 50,
    type_id: int | None = None,
    customer_id: int | None = None,
    status: str | None = None,
    search: str | None = None,
    date_from: date_type | None = None,
    date_to: date_type | None = None,
    amount_min: float | None = None,
    amount_max: float | None = None,
    ctx: Context = None,
) -> str:
    """查询销售记录列表（可按客户、业务类型、状态、日期、金额区间筛选）。

    Args:
        skip: 跳过条数（分页），默认 0。
        limit: 返回条数上限，默认 50。
        type_id: 按业务类型 ID 筛选。
        customer_id: 按客户 ID 筛选。
        status: 状态：draft=草稿 / sent=已发送 / paid=已回款。
        search: 关键字搜索（物料名称等）。
        date_from: 起始日期 YYYY-MM-DD。
        date_to: 结束日期 YYYY-MM-DD。
        amount_min: 最低金额。
        amount_max: 最高金额。
    """
    params = {"skip": skip, "limit": limit}
    params.update(
        _opt(
            dict(
                type_id=type_id,
                customer_id=customer_id,
                status=status,
                search=search,
                date_from=date_from.isoformat() if date_from else None,
                date_to=date_to.isoformat() if date_to else None,
                amount_min=amount_min,
                amount_max=amount_max,
            ),
            "type_id",
            "customer_id",
            "status",
            "search",
            "date_from",
            "date_to",
            "amount_min",
            "amount_max",
        )
    )
    data = _client(ctx).get("/sales/", params=params)
    return _json(data)


def get_sale(sale_id: int, ctx: Context = None) -> str:
    """获取单条销售记录详情。

    Args:
        sale_id: 销售记录 ID。
    """
    data = _client(ctx).get(f"/sales/{sale_id}")
    return _json(data)


# ----------------------------------------------------------------------
# Purchases
# ----------------------------------------------------------------------
def list_purchases(
    skip: int = 0,
    limit: int = 50,
    type_id: int | None = None,
    supplier_id: int | None = None,
    status: str | None = None,
    search: str | None = None,
    date_from: date_type | None = None,
    date_to: date_type | None = None,
    amount_min: float | None = None,
    amount_max: float | None = None,
    ctx: Context = None,
) -> str:
    """查询采购记录列表（可按供应商、业务类型、状态、日期、金额区间筛选）。

    Args:
        skip: 跳过条数（分页），默认 0。
        limit: 返回条数上限，默认 50。
        type_id: 按业务类型 ID 筛选。
        supplier_id: 按供应商 ID 筛选。
        status: 状态：pending=待处理 / ordered=已下单 / received=已收货。
        search: 关键字搜索（物料名称等）。
        date_from: 起始日期 YYYY-MM-DD。
        date_to: 结束日期 YYYY-MM-DD。
        amount_min: 最低金额。
        amount_max: 最高金额。
    """
    params = {"skip": skip, "limit": limit}
    params.update(
        _opt(
            dict(
                type_id=type_id,
                supplier_id=supplier_id,
                status=status,
                search=search,
                date_from=date_from.isoformat() if date_from else None,
                date_to=date_to.isoformat() if date_to else None,
                amount_min=amount_min,
                amount_max=amount_max,
            ),
            "type_id",
            "supplier_id",
            "status",
            "search",
            "date_from",
            "date_to",
            "amount_min",
            "amount_max",
        )
    )
    data = _client(ctx).get("/purchases/", params=params)
    return _json(data)


def get_purchase(purchase_id: int, ctx: Context = None) -> str:
    """获取单条采购记录详情。

    Args:
        purchase_id: 采购记录 ID。
    """
    data = _client(ctx).get(f"/purchases/{purchase_id}")
    return _json(data)


# ----------------------------------------------------------------------
# Customers / Suppliers / Companies / Departments / Types
# ----------------------------------------------------------------------
def list_customers(
    q: str | None = None,
    company_id: int | None = None,
    ctx: Context = None,
) -> str:
    """查询客户列表（按公司分组返回，company_id=0 表示个人客户）。

    Args:
        q: 客户名称关键字搜索。
        company_id: 按公司 ID 筛选。
    """
    params = _opt(dict(q=q, company_id=company_id), "q", "company_id")
    data = _client(ctx).get("/customers/", params=params)
    return _json(data)


def list_suppliers(q: str | None = None, ctx: Context = None) -> str:
    """查询供应商列表。

    Args:
        q: 供应商名称关键字搜索。
    """
    params = _opt(dict(q=q), "q")
    data = _client(ctx).get("/suppliers/", params=params)
    return _json(data)


def list_companies(q: str | None = None, ctx: Context = None) -> str:
    """查询公司列表（当前账号有权限访问的公司）。

    Args:
        q: 公司名称关键字搜索。
    """
    params = _opt(dict(q=q), "q")
    data = _client(ctx).get("/companies/", params=params)
    return _json(data)


def list_departments(company_id: int | None = None, ctx: Context = None) -> str:
    """查询部门列表。

    Args:
        company_id: 按公司 ID 筛选（可选）。
    """
    params = _opt(dict(company_id=company_id), "company_id")
    data = _client(ctx).get("/departments/", params=params)
    return _json(data)


def list_types(ctx: Context = None) -> str:
    """查询业务类型（物料分类）列表，创建销售/采购时需要传入 type_id。"""
    data = _client(ctx).get("/types/")
    return _json(data)


# Keep a reference so FastMCP can discover tools from this module cleanly.
__all__ = [
    "get_summary",
    "get_statistics",
    "list_sales",
    "get_sale",
    "list_purchases",
    "get_purchase",
    "list_customers",
    "list_suppliers",
    "list_companies",
    "list_departments",
    "list_types",
]
