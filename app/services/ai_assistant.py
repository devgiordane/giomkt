"""AI Assistant service — processes user content with OpenAI."""

import json

from app.config import OPENAI_API_KEY

PROMPTS = {
    "create_tasks": (
        "Você é um assistente de gestão de tarefas. Analise o conteúdo fornecido e "
        "extraia uma lista de tarefas acionáveis. Responda APENAS com JSON no formato: "
        '{"action": "create_tasks", "tasks": [{"title": "...", "priority": 1, "due_date": "YYYY-MM-DD ou null"}]} '
        "Prioridades: 1=urgente, 2=alta, 3=normal, 4=baixa."
    ),
    "generate_message": (
        "Você é um assistente de marketing digital. Com base no conteúdo, gere uma "
        "mensagem profissional para enviar ao cliente em português. Responda APENAS com JSON: "
        '{"action": "generate_message", "message": "...", "subject": "..."}'
    ),
    "summarize": (
        "Você é um assistente de análise. Resuma o conteúdo de forma concisa e objetiva "
        "em português. Responda APENAS com JSON: "
        '{"action": "summarize", "summary": "...", "key_points": ["..."]}'
    ),
    "extract_data": (
        "Você é um assistente de extração de dados. Extraia dados estruturados do conteúdo "
        "(nomes, valores, datas, métricas). Responda APENAS com JSON: "
        '{"action": "extract_data", "data": [{"field": "...", "value": "..."}]}'
    ),
    "analyze_campaign": (
        "Você é um especialista em marketing digital. Analise os dados da campanha e "
        "forneça insights e recomendações em português. Responda APENAS com JSON: "
        '{"action": "analyze_campaign", "analysis": "...", "recommendations": ["..."], '
        '"metrics": {"cpa": null, "ctr": null, "roas": null}}'
    ),
}


def process_content(action: str, content: str) -> dict:
    """Process user content with OpenAI based on the selected action."""
    if not OPENAI_API_KEY:
        return {"error": "OPENAI_API_KEY não configurada. Adicione no arquivo .env."}

    system_prompt = PROMPTS.get(action)
    if not system_prompt:
        return {"error": f"Ação desconhecida: {action}"}

    try:
        from openai import OpenAI

        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-5-mini-2025-08-07",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content},
            ],
            max_completion_tokens=2000,
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content.strip()
        result = json.loads(raw)
        result["_raw"] = raw
        return result

    except json.JSONDecodeError:
        return {"error": "Resposta da IA não é JSON válido.", "_raw": raw}
    except Exception as exc:
        return {"error": str(exc)}
