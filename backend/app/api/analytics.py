"""Analytics (Umami) API endpoints + Site management."""

import time

from flask import Blueprint, jsonify, request

from app.database import get_session, Site, Client

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/api/analytics/sites", methods=["GET"])
def list_sites():
    with get_session() as session:
        sites = session.query(Site).order_by(Site.name).all()
        client_map = {c.id: c.name for c in session.query(Client).all()}
        rows = [
            {
                "id": s.id,
                "name": s.name,
                "domain": s.domain,
                "umami_site_id": s.umami_site_id or "",
                "client_id": s.client_id,
                "client_name": client_map.get(s.client_id, ""),
            }
            for s in sites
        ]
        client_options = [{"id": c.id, "name": c.name} for c in session.query(Client).filter_by(status="active").order_by(Client.name).all()]
    return jsonify({"sites": rows, "client_options": client_options}), 200


@analytics_bp.route("/api/analytics/sites", methods=["POST"])
def create_site():
    body = request.get_json(force=True, silent=True) or {}
    name = (body.get("name") or "").strip()
    domain = (body.get("domain") or "").strip()
    if not name:
        return jsonify({"error": "name é obrigatório"}), 400
    if not domain:
        return jsonify({"error": "domain é obrigatório"}), 400

    with get_session() as session:
        s = Site(
            name=name,
            domain=domain,
            umami_site_id=(body.get("umami_site_id") or "").strip() or None,
            client_id=int(body["client_id"]) if body.get("client_id") else None,
        )
        session.add(s)
        session.flush()
        site_id = s.id

    return jsonify({"id": site_id}), 201


@analytics_bp.route("/api/analytics/sites/<int:site_id>", methods=["DELETE"])
def delete_site(site_id):
    with get_session() as session:
        s = session.get(Site, site_id)
        if not s:
            return jsonify({"error": "Site não encontrado"}), 404
        session.delete(s)
    return jsonify({"ok": True}), 200


@analytics_bp.route("/api/analytics/stats", methods=["GET"])
def get_stats():
    """Fetch analytics stats for a site from Umami."""
    site_id = request.args.get("site_id", type=int)
    days = request.args.get("days", type=int, default=30)

    from app.config import UMAMI_API_URL, UMAMI_API_TOKEN
    from app.services.umami import get_website_stats, get_website_pageviews, get_website_metrics

    if not UMAMI_API_URL or not UMAMI_API_TOKEN:
        return jsonify({"error": "UMAMI_API_URL e UMAMI_API_TOKEN não configurados"}), 400

    if not site_id:
        return jsonify({"error": "site_id é obrigatório"}), 400

    with get_session() as session:
        site = session.get(Site, site_id)
        if not site or not site.umami_site_id:
            return jsonify({"error": "Site sem Umami ID configurado"}), 400
        umami_id = site.umami_site_id

    end_at = int(time.time() * 1000)
    start_at = int((time.time() - days * 86400) * 1000)

    stats = get_website_stats(umami_id, start_at, end_at) or {}
    pageviews_data = get_website_pageviews(umami_id, start_at, end_at, "day") or {}
    top_pages_data = get_website_metrics(umami_id, start_at, end_at, "url") or []

    pv = stats.get("pageviews", {}).get("value", 0)
    visitors = stats.get("visitors", {}).get("value", 0)
    bounces = stats.get("bounces", {}).get("value", 0)
    totaltime = stats.get("totaltime", {}).get("value", 0)

    return jsonify({
        "kpis": {
            "pageviews": pv,
            "visitors": visitors,
            "bounce_rate": (bounces / visitors * 100) if visitors else 0,
            "avg_time_seconds": totaltime / visitors if visitors else 0,
        },
        "pageviews_by_day": pageviews_data.get("pageviews", []),
        "top_pages": top_pages_data[:10],
    }), 200
