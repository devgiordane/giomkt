"""Goals API endpoints."""

from datetime import date, timedelta

from flask import Blueprint, jsonify, request
from sqlalchemy import func, extract

from app.database import get_session, ProductGoal, Sale, Product

goals_bp = Blueprint("goals", __name__)


def _goal_progress(session, g, month, year, view_mode="commission"):
    product = session.get(Product, g.product_id)
    if not product:
        return None

    actual_count = session.query(
        func.coalesce(func.sum(Sale.quantity), 0)
    ).filter(
        Sale.product_id == g.product_id,
        extract("month", Sale.date) == month,
        extract("year", Sale.date) == year,
    ).scalar() or 0

    actual_revenue = session.query(
        func.coalesce(func.sum(Sale.value), 0)
    ).filter(
        Sale.product_id == g.product_id,
        extract("month", Sale.date) == month,
        extract("year", Sale.date) == year,
    ).scalar() or 0

    actual_commission = session.query(
        func.coalesce(func.sum(Sale.commission_value), 0)
    ).filter(
        Sale.product_id == g.product_id,
        extract("month", Sale.date) == month,
        extract("year", Sale.date) == year,
    ).scalar() or 0

    today = date.today()
    past_months_revenue = session.query(
        func.coalesce(func.sum(Sale.value), 0)
    ).filter(
        Sale.product_id == g.product_id,
        Sale.date >= today - timedelta(days=90),
        Sale.date < today.replace(day=1),
    ).scalar() or 0

    past_months_commission = session.query(
        func.coalesce(func.sum(Sale.commission_value), 0)
    ).filter(
        Sale.product_id == g.product_id,
        Sale.date >= today - timedelta(days=90),
        Sale.date < today.replace(day=1),
    ).scalar() or 0

    avg_revenue = past_months_revenue / 3 if past_months_revenue else 0
    avg_commission = past_months_commission / 3 if past_months_commission else 0

    is_comm = view_mode == "commission"
    target_val = g.commission_target if is_comm else g.revenue_target
    actual_val = actual_commission if is_comm else actual_revenue
    avg_val = avg_commission if is_comm else avg_revenue

    sales_pct = min(int(actual_count / g.sales_target * 100), 100) if g.sales_target else 0
    val_pct = min(int(actual_val / target_val * 100), 100) if target_val else 0

    return {
        "id": g.id,
        "product_id": g.product_id,
        "product_name": product.name,
        "month": g.month,
        "year": g.year,
        "sales_target": g.sales_target,
        "revenue_target": g.revenue_target,
        "commission_target": g.commission_target,
        "actual_sales": actual_count,
        "actual_revenue": actual_revenue,
        "actual_commission": actual_commission,
        "avg_revenue_3m": avg_revenue,
        "avg_commission_3m": avg_commission,
        "sales_pct": sales_pct,
        "val_pct": val_pct,
        "target_val": target_val,
        "actual_val": actual_val,
        "avg_val": avg_val,
    }


@goals_bp.route("/api/goals", methods=["GET"])
def list_goals():
    month = request.args.get("month", type=int, default=date.today().month)
    year = request.args.get("year", type=int, default=date.today().year)
    view_mode = request.args.get("view_mode", "commission")
    sort_mode = request.args.get("sort_mode", "default")

    with get_session() as session:
        goals = session.query(ProductGoal).filter_by(month=month, year=year).all()
        result = [_goal_progress(session, g, month, year, view_mode) for g in goals]
        result = [r for r in result if r]

    if sort_mode == "closest":
        result.sort(key=lambda x: (x["sales_pct"], x["actual_sales"]), reverse=True)
    elif sort_mode == "farthest":
        result.sort(key=lambda x: (x["sales_pct"], x["actual_sales"]), reverse=False)

    return jsonify(result), 200


@goals_bp.route("/api/goals", methods=["POST"])
def upsert_goal():
    body = request.get_json(force=True, silent=True) or {}
    if not body.get("product_id"):
        return jsonify({"error": "product_id é obrigatório"}), 400

    product_id = int(body["product_id"])
    month = int(body.get("month", date.today().month))
    year = int(body.get("year", date.today().year))

    with get_session() as session:
        existing = session.query(ProductGoal).filter_by(
            product_id=product_id, month=month, year=year
        ).first()
        if existing:
            existing.sales_target = int(body.get("sales_target") or 0)
            existing.revenue_target = float(body.get("revenue_target") or 0)
            existing.commission_target = float(body.get("commission_target") or 0)
            goal_id = existing.id
        else:
            g = ProductGoal(
                product_id=product_id,
                month=month,
                year=year,
                sales_target=int(body.get("sales_target") or 0),
                revenue_target=float(body.get("revenue_target") or 0),
                commission_target=float(body.get("commission_target") or 0),
            )
            session.add(g)
            session.flush()
            goal_id = g.id

    return jsonify({"id": goal_id}), 200
