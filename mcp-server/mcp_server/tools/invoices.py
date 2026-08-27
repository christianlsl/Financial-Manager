"""Invoice (.xlsx) generation MCP tools.

Batch export produces a sales table workbook that matches the frontend
download layout and preserves every field returned by the sales API.
The file is saved under the configured invoice directory and is also
returned to the MCP client as a binary attachment (EmbeddedResource)
so WorkBuddy can present it for download.
"""

from __future__ import annotations

import base64
import json
from datetime import date as date_type
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

from mcp.server.fastmcp import Context

from ..api_client import get_client as _get_client
from ..api_client import session_key
from ..config import settings


def _client(ctx: Context):
    """Backend client bound to the current user's session."""
    return _get_client(session_key(ctx))

STATUS_CN = {
    "draft": "草稿",
    "sent": "已发送",
    "paid": "已回款",
    "pending": "待处理",
    "ordered": "已下单",
    "received": "已收货",
}

_FONT_TITLE = Font(name="微软雅黑", size=18, bold=True, color="1F4E79")
_FONT_HEADER = Font(name="微软雅黑", size=11, bold=True, color="1F4E79")
_FONT_BODY = Font(name="微软雅黑", size=11)
_FONT_SMALL = Font(name="微软雅黑", size=9, color="808080")
_FILL_HEADER = PatternFill("solid", fgColor="DDEBF7")
_FILL_TOTAL = PatternFill("solid", fgColor="FFF2CC")
_THIN = Side(style="thin", color="B0B0B0")
_BORDER = Border(left=_THIN, right=_THIN, top=_THIN, bottom=_THIN)
_CENTER = Alignment(horizontal="center", vertical="center")
_LEFT = Alignment(horizontal="left", vertical="center")
_RIGHT = Alignment(horizontal="right", vertical="center")

_BASE_EXPORT_COLUMNS = [
    ("date", "日期", 15),
    ("item_name", "项目", 30),
    ("company_name", "公司", 30),
    ("department_name", "部门", 15),
    ("customer_name", "客户", 15),
    ("type_name", "类型", 15),
    ("items_count", "数量", 10),
    ("unit_price", "单价", 15),
    ("total_price", "金额", 15),
    ("image", "图片", 28),
    ("status", "状态", 15),
    ("notes", "备注", 30),
]
_BASE_EXPORT_KEYS = [key for key, _, _ in _BASE_EXPORT_COLUMNS]


def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, default=str)


def _amount(value: Any) -> str:
    """Format a numeric value as 1,234.56."""
    try:
        return f"{Decimal(str(value)):,.2f}"
    except Exception:
        return str(value)


def _coerce_export_value(key: str, value: Any) -> Any:
    if value is None:
        return ""
    if key == "status":
        return STATUS_CN.get(str(value), str(value))
    if key in {"items_count"}:
        try:
            return int(Decimal(str(value)))
        except Exception:
            return value
    if key in {"unit_price", "total_price"}:
        try:
            return float(Decimal(str(value)))
        except Exception:
            return value
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False, default=str)
    if isinstance(value, (datetime, date_type)):
        return value.isoformat()
    return value


def _build_batch_workbook(items: list[dict[str, Any]]) -> Workbook:
    wb = Workbook()
    ws = wb.active
    ws.title = "销售表"

    extra_keys: list[str] = []
    seen_keys = set(_BASE_EXPORT_KEYS)
    for item in items:
        for key in item.keys():
            if key not in seen_keys:
                seen_keys.add(key)
                extra_keys.append(key)

    export_columns = _BASE_EXPORT_COLUMNS + [(key, key, 18) for key in extra_keys]
    for idx, (_, _, width) in enumerate(export_columns, start=1):
        ws.column_dimensions[ws.cell(row=1, column=idx).column_letter].width = width

    for column_index, (_, label, _) in enumerate(export_columns, start=1):
        cell = ws.cell(row=1, column=column_index, value=label)
        cell.font = _FONT_HEADER
        cell.fill = _FILL_HEADER
        cell.alignment = _CENTER
        cell.border = _BORDER

    for row_index, item in enumerate(items, start=2):
        row = dict(item)
        row["image"] = item.get("image_url") or item.get("image") or ""
        for column_index, (key, _, _) in enumerate(export_columns, start=1):
            if key == "image":
                image_url = item.get("image_url") or item.get("image") or ""
                value = "图片" if image_url else "无"
            else:
                value = _coerce_export_value(key, row.get(key))

            cell = ws.cell(row=row_index, column=column_index, value=value)
            cell.font = _FONT_BODY
            cell.border = _BORDER
            if key == "image" and (item.get("image_url") or item.get("image")):
                cell.hyperlink = str(item.get("image_url") or item.get("image"))
                cell.font = Font(name="微软雅黑", size=11, color="0563C1", underline="single")
            if key in {"items_count"}:
                cell.alignment = _CENTER
            elif key in {"unit_price", "total_price"}:
                cell.alignment = _RIGHT
            else:
                cell.alignment = _LEFT

    return wb


def _save_and_attachment(wb: Workbook, file_stem: str) -> tuple[str, str]:
    """Save workbook to disk and build a base64 attachment payload."""
    settings.invoice_dir.mkdir(parents=True, exist_ok=True)
    path = settings.invoice_dir / f"{file_stem}.xlsx"
    wb.save(path)
    raw = path.read_bytes()
    b64 = base64.b64encode(raw).decode("ascii")
    return str(path), b64


def _coerce_date(value: date_type | str | None) -> str | None:
    """Accept a date object or an ISO-format string, return ISO string."""
    if value is None:
        return None
    if isinstance(value, date_type):
        return value.isoformat()
    return date_type.fromisoformat(str(value).strip()).isoformat()


def generate_invoices_batch(
    date_from: date_type | str | None = None,
    date_to: date_type | str | None = None,
    company_id: int | None = None,
    customer_id: int | None = None,
    status: str | None = None,
    limit: int = 50,
    ctx: Context = None,
) -> Any:
    """批量导出销售表格，字段和前端下载保持一致。

    用于月末/周报批量导出。文件数量受 limit 限制，最多 200 条。

    Args:
        date_from: 起始日期 YYYY-MM-DD。
        date_to: 结束日期 YYYY-MM-DD。
        company_id: 仅导出该公司的销售记录。
        customer_id: 仅生成该客户的账单。
        status: 仅生成该状态的账单：draft / sent / paid。
        limit: 最多生成多少个账单，默认 50，最大 200。
    """
    limit = max(1, min(int(limit), 200))
    params: dict[str, Any] = {"skip": 0, "limit": limit}
    d_from = _coerce_date(date_from)
    d_to = _coerce_date(date_to)
    if d_from:
        params["date_from"] = d_from
    if d_to:
        params["date_to"] = d_to
    if company_id is not None:
        params["company_id"] = company_id
    if customer_id is not None:
        params["customer_id"] = customer_id
    if status:
        params["status"] = status

    data = _client(ctx).get("/sales/", params=params)
    items = data.get("items", [])
    if not items:
        return _json({"message": "没有符合条件的销售记录，未生成表格"})

    wb = _build_batch_workbook(items)
    file_stem = f"销售表格_{datetime.now():%Y-%m-%d_%H%M%S}"
    path, b64 = _save_and_attachment(wb, file_stem)

    total_amount = Decimal("0")
    for sale in items:
        try:
            total_amount += Decimal(str(sale.get("total_price") or 0))
        except Exception:
            continue

    summary = (
        f"已导出 {len(items)} 条销售记录：\n"
        f"{path}\n"
        f"合计金额：{_amount(total_amount)} 元"
    )
    return _attachment_response(summary, file_stem, b64)


def _attachment_response(summary: str, base_name: str, blobs: str | list[str]) -> Any:
    """Return an MCP response that includes the xlsx files as attachments.

    Uses CallToolResult(EmbeddedResource(BlobResourceContents)) so the MCP
    client renders them as downloadable files, plus a text summary.
    """
    try:
        from mcp.types import (
            BlobResourceContents,
            CallToolResult,
            EmbeddedResource,
            TextContent,
        )

        if isinstance(blobs, str):
            blobs = [blobs]
        resources = []
        for idx, b64 in enumerate(blobs):
            name = base_name if len(blobs) == 1 else f"{base_name}_{idx + 1}"
            resources.append(
                EmbeddedResource(
                    type="resource",
                    resource=BlobResourceContents(
                        uri=f"file:///{name}.xlsx",
                        blob=b64,
                        mimeType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    ),
                )
            )
        resources.append(TextContent(type="text", text=summary))
        return CallToolResult(content=resources)
    except ImportError:
        # Fallback: plain text with base64 payload so nothing is lost.
        return _json({"summary": summary, "files": blobs})


__all__ = ["generate_invoices_batch"]
