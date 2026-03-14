"""Eduzz Webhook API service — manage subscriptions and receive events."""

import json
from typing import Optional

import requests

from app.config import EDUZZ_API_URL

WEBHOOK_BASE = f"{EDUZZ_API_URL}/webhook/v1"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _headers(account_id: int) -> dict | None:
    from app.database import get_session, EduzzAccount
    with get_session() as session:
        account = session.get(EduzzAccount, account_id)
        if not account or not account.access_token:
            return None
        return {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"bearer {account.access_token}",
        }


# ---------------------------------------------------------------------------
# Subscription CRUD (Eduzz API)
# ---------------------------------------------------------------------------

def list_subscriptions(account_id: int) -> dict:
    headers = _headers(account_id)
    if not headers:
        return {"error": "Conta não conectada."}
    try:
        resp = requests.get(f"{WEBHOOK_BASE}/subscription", headers=headers, timeout=30)
        resp.raise_for_status()
        return {"items": resp.json()}
    except Exception as exc:
        return {"error": str(exc)}


def create_subscription(account_id: int, name: str, url: str, events: list[str], filters: list[dict] | None = None) -> dict:
    headers = _headers(account_id)
    if not headers:
        return {"error": "Conta não conectada."}
    body = {
        "name": name,
        "url": url,
        "events": [{"name": e} for e in events],
    }
    if filters:
        body["filters"] = filters
    try:
        resp = requests.post(f"{WEBHOOK_BASE}/subscription", headers=headers, json=body, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        err_detail = exc
        if hasattr(exc, "response") and exc.response is not None:
            err_detail = f"{exc} | {exc.response.text}"
        return {"error": str(err_detail)}


def update_subscription(account_id: int, subscription_id: str, name: str, url: str, events: list[str], filters: list[dict] | None = None) -> dict:
    headers = _headers(account_id)
    if not headers:
        return {"error": "Conta não conectada."}
    body = {
        "name": name,
        "url": url,
        "events": [{"name": e} for e in events],
    }
    if filters:
        body["filters"] = filters
    try:
        resp = requests.put(f"{WEBHOOK_BASE}/subscription/{subscription_id}", headers=headers, json=body, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        err_detail = exc
        if hasattr(exc, "response") and exc.response is not None:
            err_detail = f"{exc} | {exc.response.text}"
        return {"error": str(err_detail)}


def delete_subscription(account_id: int, subscription_id: str) -> dict:
    headers = _headers(account_id)
    if not headers:
        return {"error": "Conta não conectada."}
    try:
        resp = requests.delete(f"{WEBHOOK_BASE}/subscription/{subscription_id}", headers=headers, timeout=30)
        resp.raise_for_status()
        return {"ok": True}
    except Exception as exc:
        return {"error": str(exc)}


def set_subscription_status(account_id: int, subscription_id: str, status: str) -> dict:
    """Enable or disable a subscription. status: 'active' | 'disabled'."""
    headers = _headers(account_id)
    if not headers:
        return {"error": "Conta não conectada."}
    try:
        resp = requests.post(
            f"{WEBHOOK_BASE}/subscription/{subscription_id}/status",
            headers=headers,
            json={"status": status},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        return {"error": str(exc)}


def send_test(account_id: int, subscription_id: str, event: str) -> dict:
    headers = _headers(account_id)
    if not headers:
        return {"error": "Conta não conectada."}
    try:
        resp = requests.post(
            f"{WEBHOOK_BASE}/subscription/sample",
            headers=headers,
            json={"subscriptionId": subscription_id, "event": event},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        return {"error": str(exc)}


def list_origins(account_id: int) -> dict:
    """List all available webhook origins and their events."""
    headers = _headers(account_id)
    if not headers:
        return {"error": "Conta não conectada."}
    try:
        resp = requests.get(f"{WEBHOOK_BASE}/origin", headers=headers, timeout=30)
        resp.raise_for_status()
        return {"items": resp.json()}
    except Exception as exc:
        return {"error": str(exc)}


def get_secret(account_id: int) -> dict:
    headers = _headers(account_id)
    if not headers:
        return {"error": "Conta não conectada."}
    try:
        resp = requests.get(f"{WEBHOOK_BASE}/secret", headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        return {"error": str(exc)}


# ---------------------------------------------------------------------------
# Local DB helpers
# ---------------------------------------------------------------------------

def sync_subscription_to_db(account_id: int, eduzz_data: dict) -> None:
    """Upsert a webhook subscription from Eduzz API data into the local DB."""
    from app.database import get_session, WebhookSubscription
    eduzz_id = eduzz_data.get("id")
    if not eduzz_id:
        return
    events_raw = eduzz_data.get("events", [])
    events_list = []
    for e in events_raw:
        if isinstance(e, dict):
            events_list.append(e.get("name", ""))
        elif isinstance(e, str):
            events_list.append(e)

    with get_session() as session:
        sub = session.query(WebhookSubscription).filter_by(eduzz_subscription_id=eduzz_id).first()
        if sub:
            sub.name = eduzz_data.get("name", sub.name)
            sub.url = eduzz_data.get("url", sub.url)
            sub.status = eduzz_data.get("status", sub.status)
            sub.events = json.dumps(events_list)
            sub.secret_id = eduzz_data.get("secretId", sub.secret_id)
        else:
            session.add(WebhookSubscription(
                account_id=account_id,
                eduzz_subscription_id=eduzz_id,
                name=eduzz_data.get("name", ""),
                url=eduzz_data.get("url", ""),
                status=eduzz_data.get("status", "disabled"),
                events=json.dumps(events_list),
                secret_id=eduzz_data.get("secretId"),
            ))


def save_received_event(event_type: str, payload: dict, subscription_id: Optional[int] = None) -> None:
    """Persist a received webhook event to the local DB."""
    from app.database import get_session, WebhookEvent
    with get_session() as session:
        session.add(WebhookEvent(
            subscription_id=subscription_id,
            event_type=event_type,
            payload=json.dumps(payload, ensure_ascii=False),
            processed=False,
        ))


def _send_flow_message(flow_template: str, sale_data: dict, buyer_data: dict, payment_data: dict) -> None:
    """Helper to format and send a message flow via WhatsApp."""
    from app.services.whatsapp import send_whatsapp_message
    
    buyer_phone = buyer_data.get("phone")
    if not buyer_phone:
        return
        
    # Replace variables in template
    # Supported variables: {name}, {product}, {value}, {pix_code}, {billet_url}
    message = flow_template
    message = message.replace("{name}", buyer_data.get("name", "").split(" ")[0])
    
    # We might need to extract product name from somewhere else if not in buyer_data
    # But usually sale_data has product.name
    product_name = sale_data.get("product", {}).get("name", "Produto")
    message = message.replace("{product}", product_name)
    
    value = float((sale_data.get("total") or {}).get("value", 0) or sale_data.get("value", 0))
    message = message.replace("{value}", f"R$ {value:,.2f}".replace(",", "_").replace(".", ",").replace("_", "."))
    
    # These would ideally come from the specific payment method details in Eduzz payload
    # For now, we put placeholders or try to extract if available
    pix_code = payment_data.get("pixCode", "código PIX (não disponível no webhook padrão)")
    billet_url = payment_data.get("billetUrl", "link do boleto (não disponível no webhook padrão)")
    
    message = message.replace("{pix_code}", pix_code)
    message = message.replace("{billet_url}", billet_url)

    # Format phone number to standard format if needed (remove +55, spaces, dashes)
    import re
    phone_clean = re.sub(r'\D', '', str(buyer_phone))
    if phone_clean.startswith('55'):
        phone_clean = phone_clean[2:]
    
    send_whatsapp_message(f"55{phone_clean}", message)

def process_sale_event(payload: dict) -> None:
    """Handle a sale-related webhook event: upsert sale data into DB and trigger message flows."""
    from app.database import get_session, Product, Sale, ProductMessageFlow
    from datetime import datetime, date

    data = payload.get("data", {})
    event_name = payload.get("event", "")

    # Only process sale/purchase events
    if not any(k in event_name for k in ("sale", "purchase", "invoice")):
        return

    sale_data = data.get("sale") or data.get("invoice") or data
    product_data = data.get("product") or sale_data.get("product") or {}
    eduzz_prod_id = str(product_data.get("id", "") or product_data.get("hash", ""))
    ext_id = str(sale_data.get("id", "") or payload.get("id", ""))

    if not ext_id:
        return

    date_str = sale_data.get("paidAt") or sale_data.get("createdAt") or sale_data.get("date")
    try:
        sale_date = datetime.fromisoformat(date_str.replace("Z", "+00:00")).date() if date_str else date.today()
    except Exception:
        sale_date = date.today()

    value = float((sale_data.get("total") or {}).get("value", 0) or sale_data.get("value", 0))
    commission_value = float((sale_data.get("netGain") or {}).get("value", 0) or sale_data.get("commission_value", 0))

    with get_session() as session:
        existing = session.query(Sale).filter_by(external_id=ext_id).first()
        if existing:
            existing.value = value
            existing.commission_value = commission_value
            existing.date = sale_date
            return

        product = None
        if eduzz_prod_id:
            product = session.query(Product).filter_by(product_id_eduzz=eduzz_prod_id).first()

        if not product:
            return

        session.add(Sale(
            product_id=product.id,
            date=sale_date,
            value=value,
            commission_value=commission_value,
            quantity=1,
            source="webhook",
            external_id=ext_id,
        ))
        
        # Check and trigger message flow based on status
        status = sale_data.get("status")
        if status:
            flows = session.query(ProductMessageFlow).filter_by(
                product_id=product.id, 
                status=status,
                active=True
            ).all()
            
            if flows:
                buyer = sale_data.get("buyer") or {}
                payment = sale_data.get("payment") or {}
                
                for flow in flows:
                    # In a real scenario with delay_minutes, we would schedule this.
                    # For now, we send it immediately or assume an external worker.
                    _send_flow_message(flow.template, sale_data, buyer, payment)
