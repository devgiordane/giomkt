"""AI-based message parsing using OpenAI."""

import json
from app.config import OPENAI_API_KEY


def parse_task_ai(message_text: str) -> dict:
    """
    Use OpenAI to extract a task title and description from a WhatsApp message.
    Returns a dict with 'title' and 'description' keys.
    Falls back to a simple extraction if the API call fails.
    """
    if not OPENAI_API_KEY:
        # Fallback: use first line as title, full text as description
        lines = message_text.strip().splitlines()
        title = lines[0][:200] if lines else message_text[:200]
        return {"title": title, "description": message_text}

    try:
        from openai import OpenAI

        client = OpenAI(api_key=OPENAI_API_KEY)

        system_prompt = (
            "You are an assistant that extracts task information from WhatsApp messages. "
            "Given a message, respond ONLY with a JSON object containing 'title' (string, max 200 chars) "
            "and 'description' (string). No markdown, no explanation, just the JSON."
        )

        response = client.chat.completions.create(
            model="gpt-5-mini-2025-08-07",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Message: {message_text}"},
            ],
            temperature=0.2,
            max_tokens=300,
        )

        content = response.choices[0].message.content.strip()
        parsed = json.loads(content)
        return {
            "title": str(parsed.get("title", message_text[:200])),
            "description": str(parsed.get("description", message_text)),
        }

    except Exception:
        lines = message_text.strip().splitlines()
        title = lines[0][:200] if lines else message_text[:200]
        return {"title": title, "description": message_text}
