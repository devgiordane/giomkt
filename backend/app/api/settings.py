"""Settings API endpoints (WhatsApp / EvolutionAPI)."""

import json
import os

import requests as req
from flask import Blueprint, jsonify, request

settings_bp = Blueprint("settings", __name__)

SETTINGS_FILE = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "whatsapp_settings.json"
)


def _load_settings() -> dict:
    try:
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    from app.config import EVOLUTION_API_URL, EVOLUTION_API_KEY, EVOLUTION_INSTANCE
    return {
        "base_url": EVOLUTION_API_URL,
        "api_key": EVOLUTION_API_KEY,
        "instance_name": EVOLUTION_INSTANCE,
    }


@settings_bp.route("/api/settings/whatsapp", methods=["GET"])
def get_whatsapp_settings():
    settings = _load_settings()
    # Never expose the API key in plaintext — mask it
    masked = dict(settings)
    if masked.get("api_key"):
        masked["api_key"] = "***"
    return jsonify(masked), 200


@settings_bp.route("/api/settings/whatsapp", methods=["PUT"])
def save_whatsapp_settings():
    body = request.get_json(force=True, silent=True) or {}
    base_url = (body.get("base_url") or "").strip()
    instance_name = (body.get("instance_name") or "").strip()
    api_key = (body.get("api_key") or "").strip()

    if not base_url or not instance_name:
        return jsonify({"error": "base_url e instance_name são obrigatórios"}), 400

    # If api_key is masked (unchanged), reload from file
    if api_key == "***":
        current = _load_settings()
        api_key = current.get("api_key", "")

    try:
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump({"base_url": base_url, "api_key": api_key, "instance_name": instance_name}, f, indent=2)
    except Exception as exc:
        return jsonify({"error": f"Erro ao salvar: {exc}"}), 500

    return jsonify({"ok": True}), 200


@settings_bp.route("/api/settings/whatsapp/test", methods=["POST"])
def test_whatsapp_connection():
    settings = _load_settings()
    base_url = (settings.get("base_url") or "").rstrip("/")
    api_key = settings.get("api_key", "")

    if not base_url:
        return jsonify({"error": "Base URL não configurada"}), 400

    try:
        response = req.get(
            f"{base_url}/instance/fetchInstances",
            headers={"apikey": api_key},
            timeout=10,
        )
        return jsonify({"status": response.status_code, "ok": response.status_code == 200}), 200
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
