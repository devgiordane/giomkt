"""Flask application factory."""

from flask import Flask
from app.database import init_db


def create_app():
    app = Flask(__name__)

    init_db()

    from app.api.dashboard import dashboard_bp
    from app.api.clients import clients_bp
    from app.api.tasks import tasks_bp
    from app.api.campaigns import campaigns_bp
    from app.api.sales import sales_bp
    from app.api.products import products_bp
    from app.api.goals import goals_bp
    from app.api.services import services_bp
    from app.api.notes import notes_bp
    from app.api.alerts import alerts_bp
    from app.api.analytics import analytics_bp
    from app.api.labels import labels_bp
    from app.api.eduzz import eduzz_bp
    from app.api.webhooks import webhooks_bp
    from app.api.settings import settings_bp
    from app.api.message_flows import message_flows_bp
    from app.api.ai_assistant import ai_assistant_bp

    for bp in [
        dashboard_bp, clients_bp, tasks_bp, campaigns_bp, sales_bp,
        products_bp, goals_bp, services_bp, notes_bp, alerts_bp,
        analytics_bp, labels_bp, eduzz_bp, webhooks_bp, settings_bp,
        message_flows_bp, ai_assistant_bp,
    ]:
        app.register_blueprint(bp)

    return app
