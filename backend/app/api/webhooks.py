"""Webhooks API endpoints (Eduzz subscriptions + received events + incoming webhooks)."""

import json

from flask import Blueprint, jsonify, request

from app.database import get_session, WebhookSubscription, WebhookEvent, EduzzAccount

webhooks_bp = Blueprint("webhooks", __name__)


# ---------------------------------------------------------------------------
# Incoming webhooks (EvolutionAPI + Eduzz) — migrated from main.py
# ---------------------------------------------------------------------------

@webhooks_bp.route("/api/webhooks/evolutionapi", methods=["POST"])
def evolution_webhook():
    from app.services.whatsapp import process_webhook
    data = request.get_json(force=True, silent=True) or {}
    result = process_webhook(data)
    return jsonify(result)


@webhooks_bp.route("/api/eduzz/webhook", methods=["POST"])
def eduzz_webhook_receiver():
    from app.services.eduzz_webhooks import save_received_event, process_sale_event

    data = request.get_json(force=True, silent=True) or {}
    event_type = data.get("event", "unknown")

    sub_id = None
    with get_session() as session:
        sub = session.query(WebhookSubscription).filter(
            WebhookSubscription.url.contains(request.host)
        ).first()
        if sub:
            sub_id = sub.id

    save_received_event(event_type, data, sub_id)

    try:
        process_sale_event(data)
    except Exception:
        pass

    return jsonify({"status": "received"}), 200


# ---------------------------------------------------------------------------
# Webhook Subscriptions management
# ---------------------------------------------------------------------------

@webhooks_bp.route("/api/webhooks/subscriptions", methods=["GET"])
def list_subscriptions():
    with get_session() as session:
        subs = session.query(WebhookSubscription).order_by(WebhookSubscription.id.desc()).all()
        accounts = {a.id: a.name for a in session.query(EduzzAccount).all()}

        rows = [
            {
                "id": s.id,
                "account_id": s.account_id,
                "account_name": accounts.get(s.account_id, ""),
                "eduzz_subscription_id": s.eduzz_subscription_id,
                "name": s.name,
                "url": s.url,
                "status": s.status,
                "events": json.loads(s.events) if s.events else [],
                "created_at": s.created_at.strftime("%Y-%m-%d") if s.created_at else None,
            }
            for s in subs
        ]

        account_options = [{"id": a.id, "name": a.name} for a in session.query(EduzzAccount).filter_by(active=True).all()]

    return jsonify({"subscriptions": rows, "account_options": account_options}), 200


@webhooks_bp.route("/api/webhooks/subscriptions", methods=["POST"])
def create_subscription():
    body = request.get_json(force=True, silent=True) or {}
    if not body.get("account_id"):
        return jsonify({"error": "account_id é obrigatório"}), 400
    if not body.get("name") or not body.get("url"):
        return jsonify({"error": "name e url são obrigatórios"}), 400

    from app.services.eduzz_webhooks import create_subscription as svc_create

    try:
        result = svc_create(
            account_id=int(body["account_id"]),
            name=body["name"],
            url=body["url"],
            events=body.get("events", []),
        )
        return jsonify(result), 201
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@webhooks_bp.route("/api/webhooks/subscriptions/<int:sub_id>/status", methods=["PUT"])
def set_subscription_status(sub_id):
    body = request.get_json(force=True, silent=True) or {}
    new_status = body.get("status")
    if new_status not in ("active", "disabled"):
        return jsonify({"error": "status deve ser 'active' ou 'disabled'"}), 400

    from app.services.eduzz_webhooks import set_subscription_status as svc_set_status

    try:
        result = svc_set_status(sub_id, new_status)
        return jsonify(result), 200
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@webhooks_bp.route("/api/webhooks/subscriptions/<int:sub_id>", methods=["DELETE"])
def delete_subscription(sub_id):
    from app.services.eduzz_webhooks import delete_subscription as svc_delete

    try:
        result = svc_delete(sub_id)
        return jsonify(result), 200
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@webhooks_bp.route("/api/webhooks/subscriptions/<int:sub_id>/test", methods=["POST"])
def test_subscription(sub_id):
    body = request.get_json(force=True, silent=True) or {}
    event_name = body.get("event")

    from app.services.eduzz_webhooks import send_test as svc_test

    try:
        result = svc_test(sub_id, event_name)
        return jsonify(result), 200
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


# ---------------------------------------------------------------------------
# Received events
# ---------------------------------------------------------------------------

@webhooks_bp.route("/api/webhooks/events", methods=["GET"])
def list_events():
    limit = request.args.get("limit", type=int, default=100)
    sub_id = request.args.get("subscription_id", type=int)

    with get_session() as session:
        q = session.query(WebhookEvent).order_by(WebhookEvent.received_at.desc())
        if sub_id:
            q = q.filter_by(subscription_id=sub_id)
        events = q.limit(limit).all()

        rows = [
            {
                "id": e.id,
                "subscription_id": e.subscription_id,
                "event_type": e.event_type,
                "processed": e.processed,
                "received_at": e.received_at.strftime("%Y-%m-%dT%H:%M:%S") if e.received_at else None,
                "payload_preview": e.payload[:200] if e.payload else "",
            }
            for e in events
        ]

    return jsonify(rows), 200
