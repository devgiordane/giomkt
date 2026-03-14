"""Flask REST API entry point."""

import sys
import os

# Ensure the project root is on the path when running as `python app/main.py`
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app

app = create_app()


@app.route("/api/health", methods=["GET"])
def health():
    from flask import jsonify
    return jsonify({"status": "ok", "service": "giomkt"})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)
