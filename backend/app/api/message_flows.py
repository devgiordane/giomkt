"""Message Flows API endpoints."""

from flask import Blueprint, jsonify, request

from app.database import get_session, ProductMessageFlow, Product

message_flows_bp = Blueprint("message_flows", __name__)

STATUS_OPTIONS = [
    "waitingPayment", "paid", "canceled", "recovering", "refunded", "expired"
]


@message_flows_bp.route("/api/message-flows", methods=["GET"])
def list_flows():
    product_id = request.args.get("product_id", type=int)

    with get_session() as session:
        q = session.query(ProductMessageFlow)
        if product_id:
            q = q.filter_by(product_id=product_id)
        flows = q.all()

        rows = [
            {
                "id": f.id,
                "product_id": f.product_id,
                "product_name": f.product.name if f.product else "",
                "status": f.status,
                "template": f.template,
                "active": f.active,
                "delay_minutes": f.delay_minutes,
            }
            for f in flows
        ]

        products = session.query(Product).order_by(Product.name).all()
        product_options = [
            {"id": p.id, "name": p.name, "eduzz_id": p.product_id_eduzz}
            for p in products
        ]

    return jsonify({"flows": rows, "product_options": product_options}), 200


@message_flows_bp.route("/api/message-flows", methods=["POST"])
def create_flow():
    body = request.get_json(force=True, silent=True) or {}
    if not body.get("product_id"):
        return jsonify({"error": "product_id é obrigatório"}), 400
    template = (body.get("template") or "").strip()
    if not template:
        return jsonify({"error": "template é obrigatório"}), 400

    with get_session() as session:
        flow = ProductMessageFlow(
            product_id=int(body["product_id"]),
            status=body.get("status", "paid"),
            template=template,
            active=bool(body.get("active", True)),
            delay_minutes=int(body.get("delay_minutes", 0)),
        )
        session.add(flow)
        session.flush()
        flow_id = flow.id

    return jsonify({"id": flow_id}), 201


@message_flows_bp.route("/api/message-flows/<int:flow_id>/toggle", methods=["POST"])
def toggle_flow(flow_id):
    with get_session() as session:
        flow = session.get(ProductMessageFlow, flow_id)
        if not flow:
            return jsonify({"error": "Fluxo não encontrado"}), 404
        flow.active = not flow.active
        new_state = flow.active

    return jsonify({"active": new_state}), 200


@message_flows_bp.route("/api/message-flows/<int:flow_id>", methods=["DELETE"])
def delete_flow(flow_id):
    with get_session() as session:
        flow = session.get(ProductMessageFlow, flow_id)
        if not flow:
            return jsonify({"error": "Fluxo não encontrado"}), 404
        session.delete(flow)
    return jsonify({"ok": True}), 200
