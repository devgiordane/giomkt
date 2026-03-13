"""Main Dash application entry point."""

import sys
import os

# Ensure the project root is on the path when running as `python app/main.py`
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify
import dash
import dash_bootstrap_components as dbc

from app.database import init_db
from app.layout import create_layout


# ---------------------------------------------------------------------------
# Initialise database
# ---------------------------------------------------------------------------
init_db()

# ---------------------------------------------------------------------------
# Flask server
# ---------------------------------------------------------------------------
server = Flask(__name__)

# ---------------------------------------------------------------------------
# Dash app
# ---------------------------------------------------------------------------
app = dash.Dash(
    __name__,
    server=server,
    use_pages=True,
    pages_folder=os.path.join(os.path.dirname(__file__), "pages"),
    external_stylesheets=[
        dbc.themes.CYBORG,
        dbc.icons.BOOTSTRAP,
    ],
    suppress_callback_exceptions=True,
    title="GioMkt",
)

app.layout = create_layout()


# ---------------------------------------------------------------------------
# Flask routes
# ---------------------------------------------------------------------------

@server.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "giomkt"})


@server.route("/api/webhooks/evolutionapi", methods=["POST"])
def evolution_webhook():
    from app.services.whatsapp import process_webhook

    data = request.get_json(force=True, silent=True) or {}
    result = process_webhook(data)
    return jsonify(result)


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)
