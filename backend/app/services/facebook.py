"""Facebook / Meta Graph API integration."""

from datetime import date, datetime
import requests

from app.database import get_session, Client, AccountDailySnapshot


GRAPH_API_BASE = "https://graph.facebook.com/v19.0"


def sync_facebook_data(client_id: int) -> dict:
    """
    Fetch today's ad insights for a single client and upsert into AccountDailySnapshot.
    Returns a dict with the fetched values or an error key.
    """
    with get_session() as session:
        client = session.get(Client, client_id)
        if not client:
            return {"error": f"Client {client_id} not found"}

        if not client.fb_ad_account_id or not client.fb_token:
            return {"error": "Client missing fb_ad_account_id or fb_token"}

        url = f"{GRAPH_API_BASE}/act_{client.fb_ad_account_id}/insights"
        params = {
            "fields": "spend,impressions,clicks",
            "date_preset": "today",
            "access_token": client.fb_token,
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            return {"error": str(exc)}

        items = data.get("data", [])
        if not items:
            return {"error": "No data returned from Facebook API"}

        item = items[0]
        spend = float(item.get("spend", 0.0))
        impressions = int(item.get("impressions", 0))
        clicks = int(item.get("clicks", 0))
        today = date.today()

        # Upsert snapshot for today
        snapshot = (
            session.query(AccountDailySnapshot)
            .filter_by(client_id=client_id, date=today)
            .first()
        )
        if snapshot:
            snapshot.spend = spend
            snapshot.impressions = impressions
            snapshot.clicks = clicks
            snapshot.updated_at = datetime.utcnow()
        else:
            snapshot = AccountDailySnapshot(
                client_id=client_id,
                date=today,
                spend=spend,
                impressions=impressions,
                clicks=clicks,
            )
            session.add(snapshot)

        return {"spend": spend, "impressions": impressions, "clicks": clicks}


def sync_all_clients() -> list[dict]:
    """Sync Facebook data for all active clients."""
    with get_session() as session:
        clients = session.query(Client).filter_by(status="active").all()
        client_ids = [c.id for c in clients]

    results = []
    for cid in client_ids:
        result = sync_facebook_data(cid)
        result["client_id"] = cid
        results.append(result)
    return results
