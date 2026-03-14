"""Dashboard API endpoints."""

from datetime import date, timedelta

from flask import Blueprint, jsonify

from app.database import get_session, Client, AccountDailySnapshot, Task

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/api/dashboard/kpis", methods=["GET"])
def get_kpis():
    today = date.today()
    seven_days_ago = today - timedelta(days=6)

    with get_session() as session:
        total_clients = session.query(Client).count()

        today_snapshots = (
            session.query(AccountDailySnapshot)
            .filter(AccountDailySnapshot.date == today)
            .all()
        )
        spend_today = sum(s.spend for s in today_snapshots)
        active_campaigns = len(today_snapshots)

        pending_tasks = session.query(Task).filter_by(status="pending").count()

        snapshots_7d = (
            session.query(AccountDailySnapshot)
            .filter(
                AccountDailySnapshot.date >= seven_days_ago,
                AccountDailySnapshot.date <= today,
            )
            .all()
        )

    daily: dict[date, float] = {}
    for d in range(7):
        day = seven_days_ago + timedelta(days=d)
        daily[day] = 0.0
    for snap in snapshots_7d:
        daily[snap.date] = daily.get(snap.date, 0.0) + snap.spend

    dates = sorted(daily.keys())
    spend_chart = [
        {"date": d.strftime("%Y-%m-%d"), "label": d.strftime("%d/%m"), "spend": daily[d]}
        for d in dates
    ]

    return jsonify({
        "total_clients": total_clients,
        "spend_today": spend_today,
        "active_campaigns": active_campaigns,
        "pending_tasks": pending_tasks,
        "spend_chart_7d": spend_chart,
    }), 200
