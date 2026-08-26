"""Invoice (.xlsx) generation MCP tools.

A formal sales bill is produced from a sale record via openpyxl:
company header, customer info, item details, amount totals and remarks.
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


def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, default=str)


def _amount(value: Any) -> str:
    """Format a numeric value as 1,234.56."""
    try:
        return f"{Decimal(str(value)):,.2f}"
    except Exception:
        return str(value)


def _company_name(ctx: Context) -> str:
    """The bill header uses the logged-in user's company name."""
    me = _client(ctx).get("/auth/me")
    return me.get("company_name") or "财务管理"


def _build_workbook(sale: dict, company_name: str, kind: str = "销售") -> Workbook:
    wb = Workbook()
    ws = wb.active
    ws.title = "账单"

    title = "销 售 账 单" if kind == "销售" else "采 购 账 单"
    bill_no = f"{kind[:1]}-{sale['id']:06d}"
    status = STATUS_CN.get(sale.get("status", ""), sale.get("status", ""))

    # Column widths
    for col, width in zip("ABCDEF", (8, 32, 12, 16, 16, 28)):
        ws.column_dimensions[col].width = width

    # Row 1: title
    ws.merge_cells("A1:F1")
    c = ws["A1"]
    c.value = title
    c.font = _FONT_TITLE
    c.alignment = _CENTER
    ws.row_dimensions[1].height = 36

    # Row 2: company header
    ws.merge_cells("A2:F2")
    c = ws["A2"]
    c.value = f"开单单位：{company_name}"
    c.font = _FONT_HEADER
    c.alignment = _CENTER
    ws.row_dimensions[2].height = 22

    # Row 3: bill meta
    ws.merge_cells("A3:F3")
    c = ws["A3"]
    c.value = (
        f"账单编号：{bill_no}    开单日期：{sale['date']}    "
        f"状态：{status}    生成时间：{datetime.now():%Y-%m-%d %H:%M}"
    )
    c.font = _FONT_SMALL
    c.alignment = _CENTER
    ws.row_dimensions[3].height = 18

    # Row 4: blank spacer
    ws.row_dimensions[4].height = 8

    # Row 5: customer / supplier info
    if kind == "销售":
        counterparty = sale.get("customer_name") or "个人客户"
        org = sale.get("company_name") or ""
        info_lines = f"客户：{counterparty}    所属公司：{org}"
    else:
        counterparty = sale.get("supplier_name") or ""
        info_lines = f"供应商：{counterparty}"
    ws.merge_cells("A5:F5")
    c = ws["A5"]
    c.value = info_lines
    c.font = _FONT_BODY
    c.alignment = _LEFT

    # Row 6: table header
    headers = ["序号", "物料名称", "数量", "单价（元）", "金额（元）", "备注"]
    for idx, h in enumerate(headers, start=1):
        cell = ws.cell(row=6, column=idx, value=h)
        cell.font = _FONT_HEADER
        cell.fill = _FILL_HEADER
        cell.alignment = _CENTER
        cell.border = _BORDER
    ws.row_dimensions[6].height = 22

    # Row 7: item row
    item_name = sale.get("item_name") or ""
    items_count = sale.get("items_count")
    unit_price = sale.get("unit_price")
    total_price = sale.get("total_price")
    notes = sale.get("notes") or ""
    values = ["1", item_name, items_count, _amount(unit_price), _amount(total_price), notes]
    for idx, v in enumerate(values, start=1):
        cell = ws.cell(row=7, column=idx, value=v)
        cell.font = _FONT_BODY
        cell.border = _BORDER
        cell.alignment = _CENTER if idx in (1, 3) else _LEFT if idx in (2, 6) else _RIGHT
    ws.row_dimensions[7].height = 22

    # Row 8: total row
    ws.merge_cells("A8:D8")
    total_label = ws["A8"]
    total_label.value = "合计"
    total_label.font = _FONT_HEADER
    total_label.fill = _FILL_TOTAL
    total_label.alignment = _RIGHT
    total_label.border = _BORDER
    for col in ("B8", "C8", "D8"):
        ws[col].fill = _FILL_TOTAL
        ws[col].border = _BORDER
    total_cell = ws["E8"]
    total_cell.value = _amount(total_price)
    total_cell.font = Font(name="微软雅黑", size=12, bold=True, color="C00000")
    total_cell.fill = _FILL_TOTAL
    total_cell.alignment = _RIGHT
    total_cell.border = _BORDER
    ws["F8"].fill = _FILL_TOTAL
    ws["F8"].border = _BORDER
    ws.row_dimensions[8].height = 24

    # Row 10: remarks
    if notes:
        ws.merge_cells("A10:F10")
        c = ws["A10"]
        c.value = f"备注：{notes}"
        c.font = _FONT_SMALL
        c.alignment = _LEFT

    return wb


def _save_and_attachment(wb: Workbook, bill_no: str, kind: str) -> tuple[str, str]:
    """Save workbook to disk and build a base64 attachment payload."""
    settings.invoice_dir.mkdir(parents=True, exist_ok=True)
    path = settings.invoice_dir / f"{bill_no}.xlsx"
    wb.save(path)
    raw = path.read_bytes()
    b64 = base64.b64encode(raw).decode("ascii")
    return str(path), b64


def generate_invoice(sale_id: int, ctx: Context = None) -> Any:
    """根据销售记录生成一份正式的 xlsx 账单（可直接发给客户）。

    会返回 xlsx 文件供下载，同时给出账单摘要。适合单条开票场景。

    Args:
        sale_id: 销售记录 ID。
    """
    sale = _client(ctx).get(f"/sales/{sale_id}")
    wb = _build_workbook(sale, _company_name(ctx), kind="销售")
    bill_no = f"销-{sale_id:06d}"
    path, b64 = _save_and_attachment(wb, bill_no, "销售")

    summary = (
        f"账单已生成：{path}\n"
        f"账单编号：{bill_no}\n"
        f"客户：{sale.get('customer_name') or '个人客户'}\n"
        f"物料：{sale.get('item_name')}  数量：{sale.get('items_count')}  "
        f"单价：{_amount(sale.get('unit_price'))}  "
        f"金额：{_amount(sale.get('total_price'))} 元\n"
        f"状态：{STATUS_CN.get(sale.get('status', ''), sale.get('status', ''))}"
    )
    return _attachment_response(summary, bill_no, b64)


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
    customer_id: int | None = None,
    status: str | None = None,
    limit: int = 50,
    ctx: Context = None,
) -> Any:
    """批量生成销售账单（按日期范围/客户筛选），每单一个 xlsx 文件。

    用于月末/周报批量开票。文件数量受 limit 限制，最多 200 个。

    Args:
        date_from: 起始日期 YYYY-MM-DD。
        date_to: 结束日期 YYYY-MM-DD。
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
    if customer_id is not None:
        params["customer_id"] = customer_id
    if status:
        params["status"] = status

    data = _client(ctx).get("/sales/", params=params)
    items = data.get("items", [])
    if not items:
        return _json({"message": "没有符合条件的销售记录，未生成账单"})

    company_name = _company_name(ctx)
    paths: list[str] = []
    attachments: list[str] = []
    total_amount = Decimal("0")
    for sale in items:
        wb = _build_workbook(sale, company_name, kind="销售")
        bill_no = f"销-{sale['id']:06d}"
        path, b64 = _save_and_attachment(wb, bill_no, "销售")
        paths.append(path)
        attachments.append(b64)
        total_amount += Decimal(str(sale.get("total_price") or 0))

    summary = (
        f"已生成 {len(items)} 份账单：\n" + "\n".join(paths)
        + f"\n合计金额：{_amount(total_amount)} 元"
    )
    return _attachment_response(summary, "批量账单", attachments)


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


__all__ = ["generate_invoice", "generate_invoices_batch"]
