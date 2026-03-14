"""Notes API endpoints."""

from flask import Blueprint, jsonify, request

from app.database import get_session, Note, Client

notes_bp = Blueprint("notes", __name__)


@notes_bp.route("/api/notes", methods=["GET"])
def list_notes():
    client_id = request.args.get("client_id", type=int)
    wiki_only = request.args.get("wiki", "false").lower() == "true"
    limit = request.args.get("limit", type=int, default=100)

    with get_session() as session:
        q = session.query(Note).order_by(Note.created_at.desc())
        if client_id:
            q = q.filter_by(client_id=client_id)
        elif wiki_only:
            q = q.filter(Note.client_id.is_(None))
        q = q.limit(limit)
        notes = q.all()

        client_map = {c.id: c.name for c in session.query(Client).all()}

        rows = [
            {
                "id": n.id,
                "content": n.content,
                "client_id": n.client_id,
                "client_name": client_map.get(n.client_id) if n.client_id else None,
                "created_at": n.created_at.strftime("%Y-%m-%dT%H:%M:%S") if n.created_at else None,
            }
            for n in notes
        ]

        client_options = [{"id": c.id, "name": c.name} for c in session.query(Client).order_by(Client.name).all()]

    return jsonify({"notes": rows, "client_options": client_options}), 200


@notes_bp.route("/api/notes", methods=["POST"])
def create_note():
    body = request.get_json(force=True, silent=True) or {}
    content = (body.get("content") or "").strip()
    if not content:
        return jsonify({"error": "content é obrigatório"}), 400

    with get_session() as session:
        note = Note(
            content=content,
            client_id=int(body["client_id"]) if body.get("client_id") else None,
        )
        session.add(note)
        session.flush()
        note_id = note.id

    return jsonify({"id": note_id}), 201


@notes_bp.route("/api/notes/<int:note_id>", methods=["DELETE"])
def delete_note(note_id):
    with get_session() as session:
        note = session.get(Note, note_id)
        if not note:
            return jsonify({"error": "Nota não encontrada"}), 404
        session.delete(note)
    return jsonify({"ok": True}), 200
