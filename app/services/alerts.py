"""Budget alert checking service."""

from datetime import date, datetime

from app.database import (
    get_session,
    Client,
    ClientBudgetConfig,
    AccountDailySnapshot,
    AlertRule,
    Alert,
)
from app.services.whatsapp import send_whatsapp_message


def check_budget_alerts() -> list[dict]:
    """
    Query today's AccountDailySnapshot for all active clients.
    Compare spend against ClientBudgetConfig thresholds.
    Create Alert records and optionally send WhatsApp notifications.
    Returns list of triggered alert dicts.
    """
    today = date.today()
    triggered = []

    with get_session() as session:
        clients = session.query(Client).filter_by(status="active").all()

        for client in clients:
            config: ClientBudgetConfig | None = client.budget_config
            if not config:
                continue

            snapshot: AccountDailySnapshot | None = (
                session.query(AccountDailySnapshot)
                .filter_by(client_id=client.id, date=today)
                .first()
            )
            if not snapshot:
                continue

            daily_spend = snapshot.spend
            daily_limit = config.daily_limit
            threshold_pct = config.alert_threshold_pct

            if daily_limit <= 0:
                continue

            spend_pct = (daily_spend / daily_limit) * 100

            # Check active alert rules for this client
            rules = (
                session.query(AlertRule)
                .filter_by(client_id=client.id, active=True)
                .all()
            )

            for rule in rules:
                should_alert = False
                message = ""

                if rule.rule_type == "daily_budget":
                    if spend_pct >= rule.threshold:
                        should_alert = True
                        message = (
                            f"[GioMkt] Cliente '{client.name}': gasto diário atingiu "
                            f"{spend_pct:.1f}% do limite (R${daily_spend:.2f} / R${daily_limit:.2f})."
                        )
                elif rule.rule_type == "monthly_budget":
                    # For monthly we'd need to sum all snapshots for the month
                    monthly_snapshots = (
                        session.query(AccountDailySnapshot)
                        .filter(
                            AccountDailySnapshot.client_id == client.id,
                            AccountDailySnapshot.date >= today.replace(day=1),
                            AccountDailySnapshot.date <= today,
                        )
                        .all()
                    )
                    monthly_spend = sum(s.spend for s in monthly_snapshots)
                    monthly_limit = config.monthly_limit
                    if monthly_limit > 0:
                        monthly_pct = (monthly_spend / monthly_limit) * 100
                        if monthly_pct >= rule.threshold:
                            should_alert = True
                            message = (
                                f"[GioMkt] Cliente '{client.name}': gasto mensal atingiu "
                                f"{monthly_pct:.1f}% do limite (R${monthly_spend:.2f} / R${monthly_limit:.2f})."
                            )

                if should_alert:
                    alert = Alert(
                        client_id=client.id,
                        rule_id=rule.id,
                        message=message,
                        triggered_at=datetime.utcnow(),
                        resolved=False,
                    )
                    session.add(alert)
                    triggered.append(
                        {"client": client.name, "rule_type": rule.rule_type, "message": message}
                    )

                    if rule.notify_whatsapp and client.phone:
                        send_whatsapp_message(client.phone, message)

    return triggered
