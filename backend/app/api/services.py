"""Services/Subscriptions API endpoints."""

from datetime import date, timedelta

from flask import Blueprint, jsonify, request

from app.database import get_session, Service, Client

services_bp = Blueprint("services", __name__)

TYPE_LABELS = {
    "dominio": "Domínio",
    "hospedagem": "Hospedagem",
    "servidor": "Servidor",
    "api": "API",
    "software": "Software",
}


@services_bp.route("/api/services", methods=["GET"])
def list_services():
    with get_session() as session:
        services = session.query(Service).all()
        client_map = {c.id: c.name for c in session.query(Client).all()}

        today = date.today()
        rows = []
        monthly_total = 0.0
        annual_total = 0.0

        for s in services:
            monthly = s.value if s.billing_cycle == "monthly" else (s.value / 12)
            annual = s.value * 12 if s.billing_cycle == "monthly" else s.value
            monthly_total += monthly
            annual_total += annual

            rows.append({
                "id": s.id,
                "name": s.name,
                "type": s.type,
                "type_label": TYPE_LABELS.get(s.type, s.type),
                "client_id": s.client_id,
                "client_name": client_map.get(s.client_id, ""),
                "value": s.value,
                "billing_cycle": s.billing_cycle,
                "due_date": s.due_date.isoformat() if s.due_date else None,
                "notes": s.notes,
            })

        exp_7 = sum(
            1 for r in rows
            if r["due_date"] and today <= date.fromisoformat(r["due_date"]) <= today + timedelta(days=7)
        )
        exp_30 = sum(
            1 for r in rows
            if r["due_date"] and today <= date.fromisoformat(r["due_date"]) <= today + timedelta(days=30)
        )

        type_costs = {}
        for r in rows:
            monthly = r["value"] if r["billing_cycle"] == "monthly" else r["value"] / 12
            type_costs[r["type_label"]] = type_costs.get(r["type_label"], 0) + monthly

        client_options = [{"id": c.id, "name": c.name} for c in session.query(Client).filter_by(status="active").order_by(Client.name).all()]

    return jsonify({
        "services": rows,
        "kpis": {
            "expiring_7d": exp_7,
            "expiring_30d": exp_30,
            "monthly_total": monthly_total,
            "annual_total": annual_total,
        },
        "costs_by_type": type_costs,
        "client_options": client_options,
    }), 200


@services_bp.route("/api/services", methods=["POST"])
def create_service():
    body = request.get_json(force=True, silent=True) or {}
    name = (body.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name é obrigatório"}), 400
    if not body.get("type"):
        return jsonify({"error": "type é obrigatório"}), 400

    with get_session() as session:
        s = Service(
            name=name,
            type=body["type"],
            client_id=int(body["client_id"]) if body.get("client_id") else None,
            value=float(body.get("value") or 0),
            billing_cycle=body.get("billing_cycle", "monthly"),
            due_date=date.fromisoformat(body["due_date"]) if body.get("due_date") else None,
            notes=body.get("notes") or None,
        )
        session.add(s)
        session.flush()
        service_id = s.id

    return jsonify({"id": service_id}), 201


@services_bp.route("/api/services/<int:service_id>", methods=["PUT"])
def update_service(service_id):
    body = request.get_json(force=True, silent=True) or {}

    with get_session() as session:
        s = session.get(Service, service_id)
        if not s:
            return jsonify({"error": "Serviço não encontrado"}), 404

        if "name" in body and body["name"].strip():
            s.name = body["name"].strip()
        if "type" in body:
            s.type = body["type"]
        if "client_id" in body:
            s.client_id = int(body["client_id"]) if body["client_id"] else None
        if "value" in body:
            s.value = float(body["value"] or 0)
        if "billing_cycle" in body:
            s.billing_cycle = body["billing_cycle"]
        if "due_date" in body:
            s.due_date = date.fromisoformat(body["due_date"]) if body["due_date"] else None
        if "notes" in body:
            s.notes = body["notes"] or None

    return jsonify({"ok": True}), 200


@services_bp.route("/api/services/<int:service_id>", methods=["DELETE"])
def delete_service(service_id):
    with get_session() as session:
        s = session.get(Service, service_id)
        if not s:
            return jsonify({"error": "Serviço não encontrado"}), 404
        session.delete(s)
    return jsonify({"ok": True}), 200
