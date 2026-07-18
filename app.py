"""
Flask backend for Hamid Ali Awan's portfolio.

Features:
- Serves the portfolio homepage
- Allows CV download
- Accepts contact form submissions
- Saves messages to messages.json
- Validates user input
"""

import json
import os
from datetime import datetime
from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    send_from_directory,
)

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MESSAGES_FILE = os.path.join(BASE_DIR, "messages.json")
CV_FOLDER = os.path.join(BASE_DIR, "static", "cv")
CV_FILE = "Hamid_Ali_Awan_CV.pdf"


def load_messages():
    """Load saved messages from JSON file."""
    if not os.path.exists(MESSAGES_FILE):
        return []

    try:
        with open(MESSAGES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def save_messages(messages):
    """Save messages to JSON file."""
    with open(MESSAGES_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f, indent=4, ensure_ascii=False)


@app.route("/")
def index():
    """Portfolio homepage."""
    return render_template("index.html")


@app.route("/download-cv")
def download_cv():
    """Download CV."""
    os.makedirs(CV_FOLDER, exist_ok=True)

    return send_from_directory(
        CV_FOLDER,
        CV_FILE,
        as_attachment=True,
    )


@app.route("/contact", methods=["POST"])
def contact():
    """Receive contact form submissions."""

    data = request.get_json(silent=True) or request.form.to_dict()

    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    subject = (data.get("subject") or "").strip()
    message = (data.get("message") or "").strip()

    # Required fields
    if not name or not email or not message:
        return jsonify({
            "ok": False,
            "error": "Name, email and message are required."
        }), 400

    # Length validation
    if (
        len(name) > 100
        or len(email) > 255
        or len(subject) > 200
        or len(message) > 2000
    ):
        return jsonify({
            "ok": False,
            "error": "One or more fields exceed the maximum allowed length."
        }), 400

    # Save message
    messages = load_messages()

    messages.append({
        "name": name,
        "email": email,
        "subject": subject,
        "message": message,
        "received_at": datetime.utcnow().isoformat() + "Z",
    })

    save_messages(messages)

    return jsonify({
        "ok": True,
        "message": "Thank you! Your message has been received."
    })


if __name__ == "__main__":
    os.makedirs(CV_FOLDER, exist_ok=True)
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
    )