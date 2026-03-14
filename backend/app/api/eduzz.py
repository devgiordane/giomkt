"""Eduzz Accounts API endpoints."""

from datetime import date, timedelta

from flask import Blueprint, jsonify, request

from app.database import get_session, EduzzAccount
from app.config import EDUZZ_CLIENT_ID, EDUZZ_REDIRECT_URI

eduzz_bp = Blueprint("eduzz", __name__)


def _auth_url(account_id: int) -> str:
    return (
        f"https://accounts.eduzz.com/oauth/authorize"
        f"?client_id={EDUZZ_CLIENT_ID}"
        f"&redirect_uri={EDUZZ_REDIRECT_URI}"
        f"&response_type=code"
        f"&state={account_id}"
    )


@eduzz_bp.route("/api/eduzz/accounts", methods=["GET"])
def list_accounts():
    with get_session() as session:
        accounts = session.query(EduzzAccount).order_by(EduzzAccount.name).all()
        rows = [
            {
                "id": a.id,
                "name": a.name,
                "email": a.email,
                "active": a.active,
                "connected": bool(a.access_token),
                "auth_url": _auth_url(a.id),
                "created_at": a.created_at.strftime("%Y-%m-%d") if a.created_at else None,
            }
            for a in accounts
        ]
    return jsonify(rows), 200


@eduzz_bp.route("/api/eduzz/accounts", methods=["POST"])
def create_account():
    body = request.get_json(force=True, silent=True) or {}
    name = (body.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name é obrigatório"}), 400

    with get_session() as session:
        account = EduzzAccount(name=name)
        session.add(account)
        session.flush()
        account_id = account.id

    return jsonify({"id": account_id, "auth_url": _auth_url(account_id)}), 201


@eduzz_bp.route("/api/eduzz/accounts/<int:account_id>", methods=["PUT"])
def update_account(account_id):
    body = request.get_json(force=True, silent=True) or {}

    with get_session() as session:
        account = session.get(EduzzAccount, account_id)
        if not account:
            return jsonify({"error": "Conta não encontrada"}), 404
        if "name" in body and body["name"].strip():
            account.name = body["name"].strip()
        if "active" in body:
            account.active = bool(body["active"])

    return jsonify({"ok": True}), 200


@eduzz_bp.route("/api/eduzz/accounts/<int:account_id>", methods=["DELETE"])
def delete_account(account_id):
    with get_session() as session:
        account = session.get(EduzzAccount, account_id)
        if not account:
            return jsonify({"error": "Conta não encontrada"}), 404
        session.delete(account)
    return jsonify({"ok": True}), 200


@eduzz_bp.route("/api/eduzz/accounts/<int:account_id>/sync", methods=["POST"])
def sync_account(account_id):
    body = request.get_json(force=True, silent=True) or {}
    start_date = body.get("start_date", date.today().replace(day=1).isoformat())
    end_date = body.get("end_date", date.today().isoformat())

    from app.services.eduzz import sync_sales

    try:
        result = sync_sales(account_id, start_date=start_date, end_date=end_date)
        return jsonify(result), 200
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@eduzz_bp.route("/api/eduzz/callback", methods=["GET"])
def eduzz_callback():
    """OAuth2 callback — exchange code for token."""
    import urllib.parse
    from flask import redirect
    from app.services.eduzz import exchange_code

    code = request.args.get("code")
    account_id = request.args.get("state")

    if not code or not account_id:
        return redirect("/eduzz/accounts?error=missing_params")

    try:
        account_id = int(account_id)
    except (ValueError, TypeError):
        return redirect("/eduzz/accounts?error=invalid_state")

    result = exchange_code(code, account_id)

    if "error" in result:
        error_msg = urllib.parse.quote(result["error"])
        return redirect(f"/eduzz/accounts?error={error_msg}")

    return redirect("/eduzz/accounts?connected=1")
