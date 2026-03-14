"""AI Assistant API endpoints."""

from datetime import date, datetime

from flask import Blueprint, jsonify, request

from app.database import get_session, Task

ai_assistant_bp = Blueprint("ai_assistant", __name__)

VALID_ACTIONS = {"create_tasks", "generate_message", "summarize", "extract_data", "analyze_campaign"}


@ai_assistant_bp.route("/api/ai/process", methods=["POST"])
def process():
    body = request.get_json(force=True, silent=True) or {}
    content = (body.get("content") or "").strip()
    action = body.get("action", "create_tasks")

    if not content:
        return jsonify({"error": "content é obrigatório"}), 400
    if action not in VALID_ACTIONS:
        return jsonify({"error": f"action inválida. Opções: {', '.join(VALID_ACTIONS)}"}), 400

    from app.services.ai_assistant import process_content

    result = process_content(action, content)

    if "error" in result:
        return jsonify(result), 500

    return jsonify(result), 200


@ai_assistant_bp.route("/api/ai/save-tasks", methods=["POST"])
def save_tasks():
    """Batch save AI-generated tasks to the database."""
    body = request.get_json(force=True, silent=True) or {}
    tasks = body.get("tasks", [])

    if not tasks:
        return jsonify({"error": "Nenhuma tarefa fornecida"}), 400

    saved_ids = []
    with get_session() as session:
        for t in tasks:
            due = None
            if t.get("due_date"):
                try:
                    due = date.fromisoformat(t["due_date"])
                except (ValueError, TypeError):
                    pass

            task = Task(
                title=t.get("title", "Sem título"),
                priority=t.get("priority", 4),
                due_date=due,
                section="Para fazer",
                status="pending",
                source="manual",
                created_at=datetime.utcnow(),
            )
            session.add(task)
            session.flush()
            saved_ids.append(task.id)

    return jsonify({"saved_count": len(saved_ids), "ids": saved_ids}), 201
