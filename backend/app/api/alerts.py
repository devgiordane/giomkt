"""Alerts and Alert Rules API endpoints."""

from flask import Blueprint, jsonify, request

from app.database import get_session, Alert, AlertRule, Client

alerts_bp = Blueprint("alerts", __name__)


# ---------------------------------------------------------------------------
# Triggered Alerts
# ---------------------------------------------------------------------------

@alerts_bp.route("/api/alerts", methods=["GET"])
def list_alerts():
    resolved = request.args.get("resolved")  # "true" | "false" | None
    limit = request.args.get("limit", type=int, default=200)

    with get_session() as session:
        q = session.query(Alert).order_by(Alert.triggered_at.desc())
        if resolved == "true":
            q = q.filter_by(resolved=True)
        elif resolved == "false":
            q = q.filter_by(resolved=False)
        alerts = q.limit(limit).all()

        client_map = {c.id: c.name for c in session.query(Client).all()}

        rows = [
            {
                "id": a.id,
                "client_id": a.client_id,
                "client_name": client_map.get(a.client_id, f"#{a.client_id}"),
                "rule_id": a.rule_id,
                "message": a.message,
                "triggered_at": a.triggered_at.strftime("%Y-%m-%dT%H:%M:%S") if a.triggered_at else None,
                "resolved": a.resolved,
            }
            for a in alerts
        ]
    return jsonify(rows), 200


@alerts_bp.route("/api/alerts/<int:alert_id>/resolve", methods=["POST"])
def resolve_alert(alert_id):
    with get_session() as session:
        alert = session.get(Alert, alert_id)
        if not alert:
            return jsonify({"error": "Alerta não encontrado"}), 404
        alert.resolved = True
    return jsonify({"ok": True}), 200


@alerts_bp.route("/api/alerts/check", methods=["POST"])
def run_check():
    from app.services.alerts import check_budget_alerts
    try:
        triggered = check_budget_alerts()
        return jsonify({"triggered_count": len(triggered), "alerts": triggered}), 200
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


# ---------------------------------------------------------------------------
# Alert Rules
# ---------------------------------------------------------------------------

@alerts_bp.route("/api/alerts/rules", methods=["GET"])
def list_rules():
    with get_session() as session:
        rules = session.query(AlertRule).order_by(AlertRule.id.desc()).all()
        client_map = {c.id: c.name for c in session.query(Client).all()}

        rows = [
            {
                "id": r.id,
                "client_id": r.client_id,
                "client_name": client_map.get(r.client_id, f"#{r.client_id}"),
                "rule_type": r.rule_type,
                "threshold": r.threshold,
                "notify_whatsapp": r.notify_whatsapp,
                "active": r.active,
            }
            for r in rules
        ]

        client_options = [{"id": c.id, "name": c.name} for c in session.query(Client).all()]

    return jsonify({"rules": rows, "client_options": client_options}), 200


@alerts_bp.route("/api/alerts/rules", methods=["POST"])
def create_rule():
    body = request.get_json(force=True, silent=True) or {}
    if not body.get("client_id"):
        return jsonify({"error": "client_id é obrigatório"}), 400
    if not body.get("threshold"):
        return jsonify({"error": "threshold é obrigatório"}), 400

    with get_session() as session:
        rule = AlertRule(
            client_id=int(body["client_id"]),
            rule_type=body.get("rule_type", "daily_budget"),
            threshold=float(body["threshold"]),
            notify_whatsapp=bool(body.get("notify_whatsapp", False)),
            active=bool(body.get("active", True)),
        )
        session.add(rule)
        session.flush()
        rule_id = rule.id

    return jsonify({"id": rule_id}), 201


@alerts_bp.route("/api/alerts/rules/<int:rule_id>", methods=["DELETE"])
def delete_rule(rule_id):
    with get_session() as session:
        rule = session.get(AlertRule, rule_id)
        if not rule:
            return jsonify({"error": "Regra não encontrada"}), 404
        session.delete(rule)
    return jsonify({"ok": True}), 200
