"""Campaigns API endpoints (Facebook Ads spend snapshots)."""

from datetime import date

from flask import Blueprint, jsonify, request

from app.database import get_session, AccountDailySnapshot, Client

campaigns_bp = Blueprint("campaigns", __name__)


@campaigns_bp.route("/api/campaigns/snapshots", methods=["GET"])
def list_snapshots():
    limit = int(request.args.get("limit", 200))

    with get_session() as session:
        client_map = {c.id: c.name for c in session.query(Client).all()}

        snapshots = (
            session.query(AccountDailySnapshot)
            .order_by(AccountDailySnapshot.date.desc(), AccountDailySnapshot.id.desc())
            .limit(limit)
            .all()
        )

        today = date.today()
        today_snapshots = [s for s in snapshots if s.date == today]

        rows = [
            {
                "id": s.id,
                "client_id": s.client_id,
                "client_name": client_map.get(s.client_id, ""),
                "date": s.date.strftime("%Y-%m-%d"),
                "spend": s.spend,
                "impressions": s.impressions,
                "clicks": s.clicks,
            }
            for s in snapshots
        ]

        today_by_client = [
            {
                "client_id": s.client_id,
                "client_name": client_map.get(s.client_id, ""),
                "spend": s.spend,
                "impressions": s.impressions,
                "clicks": s.clicks,
            }
            for s in today_snapshots
        ]

    return jsonify({
        "snapshots": rows,
        "today_by_client": today_by_client,
        "total_spend_today": sum(s["spend"] for s in today_by_client),
    }), 200
