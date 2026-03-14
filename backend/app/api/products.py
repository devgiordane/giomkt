"""Products API endpoints."""

from flask import Blueprint, jsonify, request

from app.database import get_session, Product, EduzzAccount

products_bp = Blueprint("products", __name__)


@products_bp.route("/api/products", methods=["GET"])
def list_products():
    account_id = request.args.get("account_id", type=int)

    with get_session() as session:
        q = session.query(Product)
        if account_id:
            q = q.filter_by(account_id=account_id)
        products = q.order_by(Product.name).all()

        rows = [
            {
                "id": p.id,
                "name": p.name,
                "account_id": p.account_id,
                "account_name": p.account.name if p.account else "",
                "product_id_eduzz": p.product_id_eduzz or "",
                "price": p.price,
                "commission_percent": p.commission_percent,
                "active": p.active,
            }
            for p in products
        ]

        accounts = session.query(EduzzAccount).filter_by(active=True).order_by(EduzzAccount.name).all()
        account_options = [{"id": a.id, "name": a.name} for a in accounts]

    return jsonify({"products": rows, "account_options": account_options}), 200


@products_bp.route("/api/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    with get_session() as session:
        p = session.get(Product, product_id)
        if not p:
            return jsonify({"error": "Produto não encontrado"}), 404
        data = {
            "id": p.id,
            "name": p.name,
            "account_id": p.account_id,
            "account_name": p.account.name if p.account else "",
            "product_id_eduzz": p.product_id_eduzz or "",
            "price": p.price,
            "commission_percent": p.commission_percent,
            "active": p.active,
        }
    return jsonify(data), 200


@products_bp.route("/api/products", methods=["POST"])
def create_product():
    body = request.get_json(force=True, silent=True) or {}
    name = (body.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name é obrigatório"}), 400
    if not body.get("account_id"):
        return jsonify({"error": "account_id é obrigatório"}), 400

    with get_session() as session:
        p = Product(
            name=name,
            account_id=int(body["account_id"]),
            product_id_eduzz=(body.get("product_id_eduzz") or "").strip() or None,
            price=float(body.get("price") or 0),
            commission_percent=float(body.get("commission_percent") or 0),
        )
        session.add(p)
        session.flush()
        product_id = p.id

    return jsonify({"id": product_id}), 201


@products_bp.route("/api/products/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    body = request.get_json(force=True, silent=True) or {}

    with get_session() as session:
        p = session.get(Product, product_id)
        if not p:
            return jsonify({"error": "Produto não encontrado"}), 404
        if "name" in body and body["name"].strip():
            p.name = body["name"].strip()
        if "account_id" in body:
            p.account_id = int(body["account_id"])
        if "product_id_eduzz" in body:
            p.product_id_eduzz = (body["product_id_eduzz"] or "").strip() or None
        if "price" in body:
            p.price = float(body["price"] or 0)
        if "commission_percent" in body:
            p.commission_percent = float(body["commission_percent"] or 0)
        if "active" in body:
            p.active = bool(body["active"])

    return jsonify({"ok": True}), 200


@products_bp.route("/api/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    with get_session() as session:
        p = session.get(Product, product_id)
        if not p:
            return jsonify({"error": "Produto não encontrado"}), 404
        session.delete(p)
    return jsonify({"ok": True}), 200
