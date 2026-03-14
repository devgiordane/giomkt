"""EvolutionAPI WhatsApp integration."""

from datetime import datetime
import requests

from app.config import EVOLUTION_API_URL, EVOLUTION_API_KEY, EVOLUTION_INSTANCE
from app.database import get_session, Task
from app.services.ai_parser import parse_task_ai


def send_whatsapp_message(phone: str, message: str) -> dict:
    """Send a WhatsApp message via EvolutionAPI."""
    url = f"{EVOLUTION_API_URL}/message/sendText/{EVOLUTION_INSTANCE}"
    headers = {
        "apikey": EVOLUTION_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "number": phone,
        "textMessage": {"text": message},
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.RequestException as exc:
        return {"success": False, "error": str(exc)}


def process_webhook(data: dict) -> dict:
    """
    Parse an incoming EvolutionAPI webhook payload.
    If the message text looks like a task request, create a Task record.
    Returns a dict describing what happened.
    """
    try:
        # EvolutionAPI webhook structure
        event = data.get("event", "")
        message_data = data.get("data", {})

        if event not in ("messages.upsert", "message"):
            return {"action": "ignored", "reason": f"Unhandled event: {event}"}

        message_obj = message_data.get("message", {})
        conversation = message_obj.get("conversation") or message_obj.get(
            "extendedTextMessage", {}
        ).get("text", "")

        if not conversation:
            return {"action": "ignored", "reason": "No text content in message"}

        from_number = message_data.get("key", {}).get("remoteJid", "")
        # Clean up JID to phone number
        phone = from_number.replace("@s.whatsapp.net", "").replace("@g.us", "")

        # Detect if the message is likely a task
        task_keywords = ["tarefa", "task", "fazer", "lembrar", "agendar", "criar", "to-do", "todo"]
        text_lower = conversation.lower()
        is_task = any(kw in text_lower for kw in task_keywords)

        if not is_task:
            return {"action": "ignored", "reason": "Message does not appear to be a task"}

        # Use AI to extract structured task info
        parsed = parse_task_ai(conversation)
        title = parsed.get("title", conversation[:100])
        description = parsed.get("description", conversation)

        with get_session() as session:
            task = Task(
                client_id=None,
                title=title,
                description=description,
                status="pending",
                source="whatsapp",
                created_at=datetime.utcnow(),
            )
            session.add(task)

        return {"action": "task_created", "title": title, "from": phone}

    except Exception as exc:
        return {"action": "error", "error": str(exc)}
