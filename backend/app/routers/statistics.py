import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, extract, and_
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from ..models.purchase import Purchase
from ..models.sale import Sale
from ..models.user import User
from ..models.customer import Customer

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
            extract("year", Purchase.date) == current_year,
            extract("month", Purchase.date) == current_month,
        )
        .scalar()
    )

    # 获取当月销售总额
    monthly_sale_total = (
        db.query(func.coalesce(func.sum(Sale.total_price), 0))
        .filter(
            Sale.owner_id == current_user.id,
            extract("year", Sale.date) == current_year,
            extract("month", Sale.date) == current_month,
        )
        .scalar()
    )

    # 获取年度采购总额
    yearly_purchase_total = (
        db.query(func.coalesce(func.sum(Purchase.total_price), 0))
        .filter(Purchase.owner_id == current_user.id, extract("year", Purchase.date) == current_year)
        .scalar()
    )

    # 获取年度销售总额
    yearly_sale_total = (
        db.query(func.coalesce(func.sum(Sale.total_price), 0))
        .filter(Sale.owner_id == current_user.id, extract("year", Sale.date) == current_year)
        .scalar()
    )

    # 计算利润
    monthly_profit = float(monthly_sale_total) - float(monthly_purchase_total)
    yearly_profit = float(yearly_sale_total) - float(yearly_purchase_total)

    return {
        "monthly": {
            "purchase_total": float(monthly_purchase_total),
            "sale_total": float(monthly_sale_total),
            "profit": monthly_profit,
        },
        "yearly": {
            "purchase_total": float(yearly_purchase_total),
            "sale_total": float(yearly_sale_total),
            "profit": yearly_profit,
        },
    }


@router.get("/")
def get_detailed_statistics(
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    analysis_type: Optional[str] = Query("yearly", description="分析类型: yearly(年度) 或 monthly(月度)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """获取详细的统计数据，包括趋势分析、对比分析等"""

    # 设置默认日期范围
    if not start_date or not end_date:
        end_date = date.today()
        if analysis_type == "monthly":
            # 月度分析：最近12个月
            start_date = end_date - timedelta(days=365)  # 12个月
        else:
            # 年度分析：最近6个月
            start_date = end_date - timedelta(days=180)  # 6个月
    else:
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

    # 基础过滤条件
    base_filter = and_(
        Purchase.owner_id == current_user.id, Purchase.date >= start_date, Purchase.date <= end_date
    )
    sale_base_filter = and_(Sale.owner_id == current_user.id, Sale.date >= start_date, Sale.date <= end_date)

    # 1. 获取概览数据
    purchase_total = db.query(func.coalesce(func.sum(Purchase.total_price), 0)).filter(base_filter).scalar()
    sale_total = db.query(func.coalesce(func.sum(Sale.total_price), 0)).filter(sale_base_filter).scalar()
    profit = float(sale_total) - float(purchase_total)
    profit_rate = float(profit) / float(sale_total)

    # 2. 获取趋势数据
    if analysis_type == "monthly":
        # 月度分析：按天统计
        purchase_trend = (
            db.query(
                extract("year", Purchase.date).label("year"),
                extract("month", Purchase.date).label("month"),
                extract("day", Purchase.date).label("day"),
                func.coalesce(func.sum(Purchase.total_price), 0).label("purchase_amount"),
            )
            .filter(base_filter)
            .group_by(
                extract("year", Purchase.date), extract("month", Purchase.date), extract("day", Purchase.date)
            )
            .order_by("year", "month", "day")
            .all()
        )

        sale_trend = (
            db.query(
                extract("year", Sale.date).label("year"),
                extract("month", Sale.date).label("month"),
                extract("day", Sale.date).label("day"),
                func.coalesce(func.sum(Sale.total_price), 0).label("sale_amount"),
            )
            .filter(sale_base_filter)
            .group_by(extract("year", Sale.date), extract("month", Sale.date), extract("day", Sale.date))
            .order_by("year", "month", "day")
            .all()
        )

        # 处理月度趋势数据
        trend_data = {}
        for trend in purchase_trend:
            key = f"{int(trend.year)}-{int(trend.month):02d}-{int(trend.day):02d}"
            trend_data[key] = {"purchase": float(trend.purchase_amount), "sale": 0.0}

        for trend in sale_trend:
            key = f"{int(trend.year)}-{int(trend.month):02d}-{int(trend.day):02d}"
            if key in trend_data:
                trend_data[key]["sale"] = float(trend.sale_amount)
            else:
                trend_data[key] = {"purchase": 0.0, "sale": float(trend.sale_amount)}

        # 转换为前端需要的格式
        days = sorted(trend_data.keys())
        purchase_data = [trend_data[day]["purchase"] for day in days]
        sale_data = [trend_data[day]["sale"] for day in days]
        profit_data = [trend_data[day]["sale"] - trend_data[day]["purchase"] for day in days]

        # 月度对比数据：最近30天
        comparison_days = days[-30:] if len(days) > 30 else days
        comparison_purchase_data = purchase_data[-30:] if len(purchase_data) > 30 else purchase_data
        comparison_sale_data = sale_data[-30:] if len(sale_data) > 30 else sale_data

    else:
        # 年度分析：按月统计
        monthly_trend = (
            db.query(
                extract("year", Purchase.date).label("year"),
                extract("month", Purchase.date).label("month"),
                func.coalesce(func.sum(Purchase.total_price), 0).label("purchase_amount"),
            )
            .filter(base_filter)
            .group_by(extract("year", Purchase.date), extract("month", Purchase.date))
            .order_by("year", "month")
            .all()
        )

        monthly_sale_trend = (
            db.query(
                extract("year", Sale.date).label("year"),
                extract("month", Sale.date).label("month"),
                func.coalesce(func.sum(Sale.total_price), 0).label("sale_amount"),
            )
            .filter(sale_base_filter)
            .group_by(extract("year", Sale.date), extract("month", Sale.date))
            .order_by("year", "month")
            .all()
        )

        # 处理趋势数据
        trend_data = {}
        for trend in monthly_trend:
            key = f"{int(trend.year)}-{int(trend.month):02d}"
            trend_data[key] = {"purchase": float(trend.purchase_amount), "sale": 0.0}

        for trend in monthly_sale_trend:
            key = f"{int(trend.year)}-{int(trend.month):02d}"
            if key in trend_data:
                trend_data[key]["sale"] = float(trend.sale_amount)
            else:
                trend_data[key] = {"purchase": 0.0, "sale": float(trend.sale_amount)}

        # 转换为前端需要的格式
        months = sorted(trend_data.keys())
        purchase_data = [trend_data[month]["purchase"] for month in months]
        sale_data = [trend_data[month]["sale"] for month in months]
        profit_data = [trend_data[month]["sale"] - trend_data[month]["purchase"] for month in months]

        # 年度对比数据：最近12个月
        comparison_months = months[-12:] if len(months) > 12 else months
        comparison_purchase_data = purchase_data[-12:] if len(purchase_data) > 12 else purchase_data
        comparison_sale_data = sale_data[-12:] if len(sale_data) > 12 else sale_data

    # 3. 获取分类对比数据（按业务类型）
    purchase_by_type = (
        db.query(Purchase.type, func.coalesce(func.sum(Purchase.total_price), 0).label("amount"))
        .filter(base_filter)
        .group_by(Purchase.type)
        .all()
    )

    sale_by_type = (
        db.query(Sale.type, func.coalesce(func.sum(Sale.total_price), 0).label("amount"))
        .filter(sale_base_filter)
        .group_by(Sale.type)
        .all()
    )

    # 4. 获取客户销售额分析数据
    customer_sales = []
    categories = []

    if analysis_type == "yearly":
        # 年度分析：按年份和客户分组
        customer_sales = (
            db.query(
                Customer.name.label("customer_name"),
                extract("year", Sale.date).label("year"),
                func.coalesce(func.sum(Sale.total_price), 0).label("sale_amount"),
            )
            .select_from(Sale)
            .join(Customer, Sale.customer_id == Customer.id)
            .filter(sale_base_filter)
            .group_by(Customer.name, extract("year", Sale.date))
            .order_by("year", "customer_name")
            .all()
        )

        # 获取所有年份
        years_query = (
            db.query(extract("year", Sale.date).distinct().label("year"))
            .filter(sale_base_filter)
            .order_by("year")
            .all()
        )
        categories = [str(int(year.year)) for year in years_query]
    else:
        # 月度分析：按月份和客户分组
        customer_sales = (
            db.query(
                Customer.name.label("customer_name"),
                extract("year", Sale.date).label("year"),
                extract("month", Sale.date).label("month"),
                func.coalesce(func.sum(Sale.total_price), 0).label("sale_amount"),
            )
            .select_from(Sale)
            .join(Customer, Sale.customer_id == Customer.id)
            .filter(sale_base_filter)
            .group_by(Customer.name, extract("year", Sale.date), extract("month", Sale.date))
            .order_by("year", "month", "customer_name")
            .all()
        )

        # 获取所有月份
        months_query = (
            db.query(extract("year", Sale.date).label("year"), extract("month", Sale.date).label("month"))
            .filter(sale_base_filter)
            .group_by("year", "month")
            .order_by("year", "month")
            .all()
        )
        categories = [f"{int(month.year)}-{int(month.month):02d}" for month in months_query]

    # 构建客户销售额数据结构
    customer_data = {}
    customers = set()

    for sale in customer_sales:
        customer = sale.customer_name
        customers.add(customer)

        if analysis_type == "yearly":
            key = str(int(sale.year))
        else:
            key = f"{int(sale.year)}-{int(sale.month):02d}"

        if key not in customer_data:
            customer_data[key] = {}
        customer_data[key][customer] = float(sale.sale_amount)

    # 初始化每个分类的所有客户数据（确保所有客户在每个分类都有数据点）
    customers = sorted(list(customers))
    for category in categories:
        if category not in customer_data:
            customer_data[category] = {}
        for customer in customers:
            if customer not in customer_data[category]:
                customer_data[category][customer] = 0.0

    # 计算每个客户的总销售额
    customer_totals = {}
    for customer in customers:
        total = sum(customer_data[category].get(customer, 0.0) for category in categories)
        customer_totals[customer] = total

    # 按销售额排序客户
    sorted_customers = sorted(customers, key=lambda c: customer_totals[c], reverse=True)

    # 限制最多显示客户，其余合并为others
    MAX_CUSTOMERS = 5
    top_customers = sorted_customers[:MAX_CUSTOMERS]
    others = sorted_customers[MAX_CUSTOMERS:]

    # 准备前端需要的数据格式
    customer_series = []
    for customer in top_customers:
        series_data = [customer_data[category].get(customer, 0.0) for category in categories]
        customer_series.append({"name": customer, "type": "line", "stack": "Total", "data": series_data})

    # 如果有其他客户，合并为others
    if others:
        others_data = []
        for category in categories:
            category_others_total = sum(customer_data[category].get(c, 0.0) for c in others)
            others_data.append(category_others_total)

        customer_series.append({"name": "others", "type": "line", "stack": "Total", "data": others_data})

    return {
        "overview": {
            "purchaseTotal": float(purchase_total),
            "saleTotal": float(sale_total),
            "profit": profit,
            "profitRate": profit_rate,
        },
        "trend": {
            "categories": days if analysis_type == "monthly" else months,
            "purchaseData": purchase_data,
            "saleData": sale_data,
            "analysisType": analysis_type,
        },
        "comparison": {
            "categories": comparison_days if analysis_type == "monthly" else comparison_months,
            "purchaseData": comparison_purchase_data,
            "saleData": comparison_sale_data,
            "analysisType": analysis_type,
        },
        "profit": {
            "categories": days if analysis_type == "monthly" else months,
            "profitData": profit_data,
            "analysisType": analysis_type,
        },
        "ratio": {"purchaseTotal": float(purchase_total), "saleTotal": float(sale_total)},
        "customerAnalysis": {
            "categories": categories,
            "series": customer_series,
            "analysisType": analysis_type,
        },
    }
