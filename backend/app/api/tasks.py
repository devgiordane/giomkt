"""Tasks API endpoints."""

from datetime import date, datetime

from flask import Blueprint, jsonify, request

from app.database import (
    get_session, Task, Client, TaskLabel, TaskLabelAssoc, TaskComment,
    complete_recurring_task,
)
from app.services.nlp_task import parse_task_text

tasks_bp = Blueprint("tasks", __name__)


def _task_to_dict(t, client_map=None):
    subs = [_task_to_dict(s, client_map) for s in sorted(t.subtasks, key=lambda x: (x.priority, x.created_at or datetime.min))]
    label_data = [{"id": lb.id, "name": lb.name, "color": lb.color} for lb in t.labels]
    return {
        "id": t.id,
        "title": t.title,
        "description": t.description,
        "status": t.status,
        "source": t.source,
        "priority": t.priority,
        "section": t.section or "Para fazer",
        "due_date": t.due_date.isoformat() if t.due_date else None,
        "deadline": t.deadline.isoformat() if t.deadline else None,
        "start_time": t.start_time,
        "duration_minutes": t.duration_minutes,
        "client_id": t.client_id,
        "client": (client_map or {}).get(t.client_id) if t.client_id else None,
        "recurrence": t.recurrence or "",
        "recurrence_end": t.recurrence_end.isoformat() if t.recurrence_end else None,
        "parent_id": t.parent_id,
        "subtasks": subs,
        "subtask_count": len(subs),
        "labels": label_data,
        "created_at": t.created_at.strftime("%Y-%m-%dT%H:%M:%S") if t.created_at else None,
        "completed_at": t.completed_at.strftime("%Y-%m-%dT%H:%M:%S") if t.completed_at else None,
    }


@tasks_bp.route("/api/tasks", methods=["GET"])
def list_tasks():
    priority_filter = request.args.get("priority", "all")
    status_filter = request.args.get("status")  # pending / done / all
    include_subtasks = request.args.get("include_subtasks", "false").lower() == "true"

    with get_session() as session:
        client_map = {c.id: c.name for c in session.query(Client).all()}

        query = session.query(Task)
        if not include_subtasks:
            query = query.filter(Task.parent_id.is_(None))
        if priority_filter != "all":
            query = query.filter(Task.priority == int(priority_filter))
        if status_filter and status_filter != "all":
            query = query.filter(Task.status == status_filter)

        tasks = query.order_by(Task.priority, Task.due_date, Task.created_at).all()
        result = [_task_to_dict(t, client_map) for t in tasks]

    return jsonify(result), 200


@tasks_bp.route("/api/tasks/<int:task_id>", methods=["GET"])
def get_task(task_id):
    with get_session() as session:
        task = session.get(Task, task_id)
        if not task:
            return jsonify({"error": "Tarefa não encontrada"}), 404
        client_map = {}
        if task.client_id:
            c = session.get(Client, task.client_id)
            if c:
                client_map[c.id] = c.name
        comments = [
            {
                "id": c.id,
                "content": c.content,
                "created_at": c.created_at.strftime("%Y-%m-%dT%H:%M:%S") if c.created_at else None,
            }
            for c in task.comments
        ]
        data = _task_to_dict(task, client_map)
        data["comments"] = comments
    return jsonify(data), 200


@tasks_bp.route("/api/tasks", methods=["POST"])
def create_task():
    body = request.get_json(force=True, silent=True) or {}
    title = (body.get("title") or "").strip()
    if not title:
        return jsonify({"error": "O campo 'title' é obrigatório"}), 400

    parsed = parse_task_text(title)
    clean_title = parsed["title"] or title

    due_raw = body.get("due_date") or (parsed["due_date"].isoformat() if parsed["due_date"] else None)
    priority_raw = body.get("priority") or (parsed["priority"] if parsed["priority"] < 4 else 4)
    start_time_raw = body.get("start_time") or parsed["start_time"]
    duration_raw = body.get("duration_minutes") or parsed["duration_minutes"]

    with get_session() as session:
        task = Task(
            title=clean_title,
            description=(body.get("description") or "").strip() or None,
            section=body.get("section", "Para fazer"),
            priority=int(priority_raw) if priority_raw else 4,
            due_date=date.fromisoformat(due_raw) if due_raw else None,
            deadline=date.fromisoformat(body["deadline"]) if body.get("deadline") else None,
            start_time=start_time_raw or None,
            duration_minutes=int(duration_raw) if duration_raw else None,
            client_id=int(body["client_id"]) if body.get("client_id") else None,
            parent_id=int(body["parent_id"]) if body.get("parent_id") else None,
            recurrence=body.get("recurrence") or None,
            recurrence_end=date.fromisoformat(body["recurrence_end"]) if body.get("recurrence_end") else None,
            status="pending",
            source="manual",
            created_at=datetime.utcnow(),
        )
        session.add(task)
        session.flush()
        if body.get("label_ids"):
            for lid in body["label_ids"]:
                session.add(TaskLabelAssoc(task_id=task.id, label_id=int(lid)))
        task_id = task.id

    return jsonify({"id": task_id}), 201


@tasks_bp.route("/api/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    body = request.get_json(force=True, silent=True) or {}

    with get_session() as session:
        task = session.get(Task, task_id)
        if not task:
            return jsonify({"error": "Tarefa não encontrada"}), 404

        if "title" in body:
            parsed = parse_task_text(body["title"].strip())
            task.title = parsed["title"] or body["title"].strip()
        if "description" in body:
            task.description = (body["description"] or "").strip() or None
        if "section" in body:
            task.section = body["section"]
        if "priority" in body:
            task.priority = int(body["priority"])
        if "due_date" in body:
            task.due_date = date.fromisoformat(body["due_date"]) if body["due_date"] else None
        if "deadline" in body:
            task.deadline = date.fromisoformat(body["deadline"]) if body["deadline"] else None
        if "start_time" in body:
            task.start_time = body["start_time"] or None
        if "duration_minutes" in body:
            task.duration_minutes = int(body["duration_minutes"]) if body["duration_minutes"] else None
        if "client_id" in body:
            task.client_id = int(body["client_id"]) if body["client_id"] else None
        if "recurrence" in body:
            task.recurrence = body["recurrence"] or None
        if "recurrence_end" in body:
            task.recurrence_end = date.fromisoformat(body["recurrence_end"]) if body["recurrence_end"] else None
        if "label_ids" in body:
            session.query(TaskLabelAssoc).filter_by(task_id=task.id).delete()
            session.flush()
            for lid in (body["label_ids"] or []):
                session.add(TaskLabelAssoc(task_id=task.id, label_id=int(lid)))

    return jsonify({"ok": True}), 200


@tasks_bp.route("/api/tasks/<int:task_id>/toggle", methods=["POST"])
def toggle_task(task_id):
    """Toggle task status between pending and done."""
    with get_session() as session:
        task = session.get(Task, task_id)
        if not task:
            return jsonify({"error": "Tarefa não encontrada"}), 404

        if task.status == "pending":
            if task.recurrence:
                created_next = complete_recurring_task(task_id, session)
                return jsonify({"status": "done", "next_created": created_next}), 200
            else:
                task.status = "done"
                task.completed_at = datetime.utcnow()
        else:
            task.status = "pending"
            task.completed_at = None

    return jsonify({"status": task.status}), 200


@tasks_bp.route("/api/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    with get_session() as session:
        task = session.get(Task, task_id)
        if not task:
            return jsonify({"error": "Tarefa não encontrada"}), 404
        session.delete(task)
    return jsonify({"ok": True}), 200


# --- Comments ---

@tasks_bp.route("/api/tasks/<int:task_id>/comments", methods=["POST"])
def add_comment(task_id):
    body = request.get_json(force=True, silent=True) or {}
    content = (body.get("content") or "").strip()
    if not content:
        return jsonify({"error": "Conteúdo é obrigatório"}), 400

    with get_session() as session:
        task = session.get(Task, task_id)
        if not task:
            return jsonify({"error": "Tarefa não encontrada"}), 404
        comment = TaskComment(task_id=task_id, content=content, created_at=datetime.utcnow())
        session.add(comment)
        session.flush()
        comment_id = comment.id

    return jsonify({"id": comment_id}), 201


@tasks_bp.route("/api/tasks/comments/<int:comment_id>", methods=["DELETE"])
def delete_comment(comment_id):
    with get_session() as session:
        comment = session.get(TaskComment, comment_id)
        if not comment:
            return jsonify({"error": "Comentário não encontrado"}), 404
        session.delete(comment)
    return jsonify({"ok": True}), 200


# --- Helper endpoints ---

@tasks_bp.route("/api/tasks/options", methods=["GET"])
def task_options():
    """Return client, parent task, and label options for form dropdowns."""
    with get_session() as session:
        clients = [{"id": c.id, "name": c.name} for c in session.query(Client).filter_by(status="active").all()]
        parents = [{"id": t.id, "title": t.title} for t in session.query(Task).filter(Task.parent_id.is_(None)).all()]
        labels = [{"id": lb.id, "name": lb.name, "color": lb.color} for lb in session.query(TaskLabel).order_by(TaskLabel.name).all()]
    return jsonify({"clients": clients, "parents": parents, "labels": labels}), 200


@tasks_bp.route("/api/tasks/parse", methods=["POST"])
def parse_nlp():
    """Parse NLP task text and return extracted fields."""
    body = request.get_json(force=True, silent=True) or {}
    text = (body.get("text") or "").strip()
    if not text:
        return jsonify({}), 200
    p = parse_task_text(text)
    return jsonify({
        "title": p["title"],
        "due_date": p["due_date"].isoformat() if p["due_date"] else None,
        "priority": p["priority"],
        "start_time": p["start_time"],
        "duration_minutes": p["duration_minutes"],
    }), 200
