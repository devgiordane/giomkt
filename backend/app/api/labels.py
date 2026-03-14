"""Task Labels API endpoints."""

from flask import Blueprint, jsonify, request

from app.database import get_session, TaskLabel

labels_bp = Blueprint("labels", __name__)


@labels_bp.route("/api/labels", methods=["GET"])
def list_labels():
    with get_session() as session:
        labels = session.query(TaskLabel).order_by(TaskLabel.name).all()
        rows = [{"id": lb.id, "name": lb.name, "color": lb.color} for lb in labels]
    return jsonify(rows), 200


@labels_bp.route("/api/labels", methods=["POST"])
def create_label():
    body = request.get_json(force=True, silent=True) or {}
    name = (body.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name é obrigatório"}), 400

    with get_session() as session:
        lb = TaskLabel(name=name, color=body.get("color", "#6c757d"))
        session.add(lb)
        session.flush()
        label_id = lb.id

    return jsonify({"id": label_id}), 201


@labels_bp.route("/api/labels/<int:label_id>", methods=["PUT"])
def update_label(label_id):
    body = request.get_json(force=True, silent=True) or {}

    with get_session() as session:
        lb = session.get(TaskLabel, label_id)
        if not lb:
            return jsonify({"error": "Etiqueta não encontrada"}), 404
        if "name" in body and body["name"].strip():
            lb.name = body["name"].strip()
        if "color" in body:
            lb.color = body["color"] or "#6c757d"

    return jsonify({"ok": True}), 200


@labels_bp.route("/api/labels/<int:label_id>", methods=["DELETE"])
def delete_label(label_id):
    with get_session() as session:
        lb = session.get(TaskLabel, label_id)
        if not lb:
            return jsonify({"error": "Etiqueta não encontrada"}), 404
        session.delete(lb)
    return jsonify({"ok": True}), 200
