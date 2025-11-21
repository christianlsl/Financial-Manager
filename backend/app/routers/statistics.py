import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, extract
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from ..models.purchase import Purchase
from ..models.sale import Sale
from ..models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/summary")
def get_financial_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """获取财务统计数据，包括当月和年度的采购、销售总额及利润"""
    today = date.today()
    current_year = today.year
    current_month = today.month
    
    # 获取当月采购总额
    monthly_purchase_total = (
        db.query(func.coalesce(func.sum(Purchase.total_price), 0))
        .filter(
            Purchase.owner_id == current_user.id,
            extract('year', Purchase.date) == current_year,
            extract('month', Purchase.date) == current_month
        )
        .scalar()
    )
    
    # 获取当月销售总额
    monthly_sale_total = (
        db.query(func.coalesce(func.sum(Sale.total_price), 0))
        .filter(
            Sale.owner_id == current_user.id,
            extract('year', Sale.date) == current_year,
            extract('month', Sale.date) == current_month
        )
        .scalar()
    )
    
    # 获取年度采购总额
    yearly_purchase_total = (
        db.query(func.coalesce(func.sum(Purchase.total_price), 0))
        .filter(
            Purchase.owner_id == current_user.id,
            extract('year', Purchase.date) == current_year
        )
        .scalar()
    )
    
    # 获取年度销售总额
    yearly_sale_total = (
        db.query(func.coalesce(func.sum(Sale.total_price), 0))
        .filter(
            Sale.owner_id == current_user.id,
            extract('year', Sale.date) == current_year
        )
        .scalar()
    )
    
    # 计算利润
    monthly_profit = float(monthly_sale_total) - float(monthly_purchase_total)
    yearly_profit = float(yearly_sale_total) - float(yearly_purchase_total)
    
    return {
        "monthly": {
            "purchase_total": float(monthly_purchase_total),
            "sale_total": float(monthly_sale_total),
            "profit": monthly_profit
        },
        "yearly": {
            "purchase_total": float(yearly_purchase_total),
            "sale_total": float(yearly_sale_total),
            "profit": yearly_profit
        }
    }