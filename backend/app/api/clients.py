"""Clients API endpoints."""

from datetime import date, timedelta

from flask import Blueprint, jsonify, request

from app.database import (
    get_session, Client, AccountDailySnapshot, Task, Note, ClientBudgetConfig
)

clients_bp = Blueprint("clients", __name__)


@clients_bp.route("/api/clients", methods=["GET"])
def list_clients():
    with get_session() as session:
        clients = session.query(Client).order_by(Client.id.desc()).all()
        rows = [
            {
                "id": c.id,
                "name": c.name,
                "email": c.email or "",
                "phone": c.phone or "",
                "status": c.status,
                "fb_ad_account_id": c.fb_ad_account_id or "",
                "created_at": c.created_at.strftime("%Y-%m-%d") if c.created_at else None,
            }
            for c in clients
        ]
    return jsonify(rows), 200


@clients_bp.route("/api/clients/<int:client_id>", methods=["GET"])
def get_client(client_id):
    today = date.today()
    thirty_ago = today - timedelta(days=29)

    with get_session() as session:
        client = session.get(Client, client_id)
        if not client:
            return jsonify({"error": "Cliente não encontrado"}), 404

        budget = client.budget_config
        snapshots = (
            session.query(AccountDailySnapshot)
            .filter(
                AccountDailySnapshot.client_id == client.id,
                AccountDailySnapshot.date >= thirty_ago,
            )
            .order_by(AccountDailySnapshot.date)
            .all()
        )
        tasks = (
            session.query(Task)
            .filter_by(client_id=client.id)
            .order_by(Task.created_at.desc())
            .limit(10)
            .all()
        )
        notes = (
            session.query(Note)
            .filter_by(client_id=client.id)
            .order_by(Note.created_at.desc())
            .limit(10)
            .all()
        )

        data = {
            "id": client.id,
            "name": client.name,
            "email": client.email,
            "phone": client.phone,
            "status": client.status,
            "fb_ad_account_id": client.fb_ad_account_id,
            "created_at": client.created_at.strftime("%Y-%m-%d") if client.created_at else None,
            "budget_config": {
                "daily_limit": budget.daily_limit,
                "monthly_limit": budget.monthly_limit,
                "alert_threshold_pct": budget.alert_threshold_pct,
            } if budget else None,
            "spend_history_30d": [
                {"date": s.date.strftime("%Y-%m-%d"), "spend": s.spend}
                for s in snapshots
            ],
            "recent_tasks": [
                {
                    "id": t.id,
                    "title": t.title,
                    "status": t.status,
                    "created_at": t.created_at.strftime("%Y-%m-%d") if t.created_at else None,
                }
                for t in tasks
            ],
            "recent_notes": [
                {
                    "id": n.id,
                    "content": n.content,
                    "created_at": n.created_at.strftime("%Y-%m-%dT%H:%M:%S") if n.created_at else None,
                }
                for n in notes
            ],
        }
    return jsonify(data), 200


@clients_bp.route("/api/clients", methods=["POST"])
def create_client():
    body = request.get_json(force=True, silent=True) or {}
    name = (body.get("name") or "").strip()
    if not name:
        return jsonify({"error": "O campo 'name' é obrigatório"}), 400

    with get_session() as session:
        client = Client(
            name=name,
            email=(body.get("email") or "").strip() or None,
            phone=(body.get("phone") or "").strip() or None,
            status=body.get("status", "active"),
            fb_ad_account_id=(body.get("fb_ad_account_id") or "").strip() or None,
            fb_token=(body.get("fb_token") or "").strip() or None,
        )
        session.add(client)
        session.flush()
        client_id = client.id

    return jsonify({"id": client_id, "name": name}), 201


@clients_bp.route("/api/clients/<int:client_id>", methods=["PUT"])
def update_client(client_id):
    body = request.get_json(force=True, silent=True) or {}

    with get_session() as session:
        client = session.get(Client, client_id)
        if not client:
            return jsonify({"error": "Cliente não encontrado"}), 404

        if "name" in body and body["name"].strip():
            client.name = body["name"].strip()
        if "email" in body:
            client.email = (body["email"] or "").strip() or None
        if "phone" in body:
            client.phone = (body["phone"] or "").strip() or None
        if "status" in body:
            client.status = body["status"]
        if "fb_ad_account_id" in body:
            client.fb_ad_account_id = (body["fb_ad_account_id"] or "").strip() or None
        if "fb_token" in body:
            client.fb_token = (body["fb_token"] or "").strip() or None

    return jsonify({"ok": True}), 200


@clients_bp.route("/api/clients/<int:client_id>", methods=["DELETE"])
def delete_client(client_id):
    with get_session() as session:
        client = session.get(Client, client_id)
        if not client:
            return jsonify({"error": "Cliente não encontrado"}), 404
        session.delete(client)
    return jsonify({"ok": True}), 200
