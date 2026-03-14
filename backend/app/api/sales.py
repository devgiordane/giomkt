"""Sales API endpoints."""

from datetime import date, datetime, timedelta

from flask import Blueprint, jsonify, request
from sqlalchemy import func, extract

from app.database import get_session, Sale, Product, EduzzAccount

sales_bp = Blueprint("sales", __name__)


@sales_bp.route("/api/sales", methods=["GET"])
def list_sales():
    product_id = request.args.get("product_id", type=int)
    month_filter = request.args.get("month")  # "YYYY-MM"

    with get_session() as session:
        q = session.query(Sale).join(Product)
        if product_id:
            q = q.filter(Sale.product_id == product_id)
        if month_filter:
            y, m = month_filter.split("-")
            q = q.filter(
                extract("year", Sale.date) == int(y),
                extract("month", Sale.date) == int(m),
            )
        sales = q.order_by(Sale.date.desc()).all()

        total_value = sum(s.value or 0 for s in sales)
        total_commission = sum(s.commission_value or 0 for s in sales)
        total_qty = sum(s.quantity or 0 for s in sales)
        avg_ticket = total_value / total_qty if total_qty else 0

        rows = [
            {
                "id": s.id,
                "product_id": s.product_id,
                "product": s.product.name if s.product else "",
                "date": s.date.isoformat() if s.date else None,
                "value": s.value,
                "commission_value": s.commission_value,
                "quantity": s.quantity,
                "source": s.source,
                "external_id": s.external_id,
            }
            for s in sales
        ]

        # Month options
        month_rows = session.query(
            func.distinct(func.strftime("%Y-%m", Sale.date))
        ).order_by(func.strftime("%Y-%m", Sale.date).desc()).all()
        month_options = [d[0] for d in month_rows if d[0]]

        # Product options (active)
        products = session.query(Product).filter_by(active=True).order_by(Product.name).all()
        product_options = [{"id": p.id, "name": p.name} for p in products]

    return jsonify({
        "sales": rows,
        "kpis": {
            "total_qty": total_qty,
            "total_value": total_value,
            "total_commission": total_commission,
            "avg_ticket": avg_ticket,
        },
        "month_options": month_options,
        "product_options": product_options,
    }), 200


@sales_bp.route("/api/sales", methods=["POST"])
def create_sale():
    body = request.get_json(force=True, silent=True) or {}
    if not body.get("product_id"):
        return jsonify({"error": "product_id é obrigatório"}), 400
    if not body.get("value"):
        return jsonify({"error": "value é obrigatório"}), 400

    with get_session() as session:
        sale = Sale(
            product_id=int(body["product_id"]),
            date=date.fromisoformat(body["date"]) if body.get("date") else date.today(),
            value=float(body["value"]),
            commission_value=float(body.get("commission_value", 0) or 0),
            quantity=int(body.get("quantity", 1) or 1),
            source="manual",
        )
        session.add(sale)
        session.flush()
        sale_id = sale.id

    return jsonify({"id": sale_id}), 201


@sales_bp.route("/api/sales/<int:sale_id>", methods=["DELETE"])
def delete_sale(sale_id):
    with get_session() as session:
        sale = session.get(Sale, sale_id)
        if not sale:
            return jsonify({"error": "Venda não encontrada"}), 404
        session.delete(sale)
    return jsonify({"ok": True}), 200


@sales_bp.route("/api/sales/sync", methods=["POST"])
def sync_sales():
    """Sync last N days of sales from all active Eduzz accounts."""
    body = request.get_json(force=True, silent=True) or {}
    days = int(body.get("days", 7))

    from app.services.eduzz import fetch_sales

    with get_session() as session:
        accounts = session.query(EduzzAccount).filter_by(active=True).all()
        account_ids = [a.id for a in accounts]

    if not account_ids:
        return jsonify({"error": "Nenhuma conta Eduzz ativa"}), 400

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    results = []
    for acc_id in account_ids:
        try:
            result = fetch_sales(
                acc_id,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
            )
            results.append({"account_id": acc_id, "result": result})
        except Exception as exc:
            results.append({"account_id": acc_id, "error": str(exc)})

    return jsonify({"synced": results}), 200
