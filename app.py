"""
Hamid Ali Awan Portfolio
Flask portfolio + protected admin CMS.

Production on Vercel:
- Set SUPABASE_URL and SUPABASE_KEY for persistent storage.
- Set ADMIN_USERNAME and ADMIN_PASSWORD for admin login.
Local development falls back to SQLite (portfolio.db).
"""

import os
import secrets
import sqlite3
from datetime import datetime, timezone
from functools import wraps

import requests
from dotenv import load_dotenv

# Load .env explicitly from the same folder as app.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(BASE_DIR, ".env")

load_dotenv(ENV_FILE, override=True)

from flask import (
    Flask, flash, jsonify, redirect, render_template,
    request, send_from_directory, session, url_for
)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-local-secret")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("VERCEL") == "1"

DB_FILE = os.path.join(BASE_DIR, "portfolio.db")
CV_FOLDER = os.path.join(BASE_DIR, "static", "cv")

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")


# -----------------------------
# Storage
# -----------------------------
def using_supabase():
    return bool(SUPABASE_URL and SUPABASE_KEY)


def db_connect():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_sqlite():
    conn = db_connect()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            subject TEXT NOT NULL DEFAULT '',
            message TEXT NOT NULL,
            received_at TEXT NOT NULL,
            is_read INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            tags TEXT NOT NULL DEFAULT '',
            image_url TEXT NOT NULL DEFAULT '',
            github_url TEXT NOT NULL DEFAULT '',
            live_url TEXT NOT NULL DEFAULT '',
            sort_order INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        );
    """)
    count = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
    if count == 0:
        seeds = [
            ("AI Power Consumption Prediction",
             "Machine learning system for power consumption prediction and energy recommendations.",
             "Python,Machine Learning,Flask", "", "", "", 1),
            ("SafarPakistan",
             "Travel web application for exploring and managing Pakistan travel packages.",
             "Flask,Python,HTML,CSS,JavaScript", "", "", "", 2),
            ("Student Result Prediction",
             "Machine learning project using student performance features for prediction.",
             "Python,scikit-learn,pandas", "", "", "", 3),
            ("Data Analysis Dashboard",
             "Interactive dashboard concept for exploring data and visualizing useful insights.",
             "Python,Flask,JavaScript,Charts", "", "", "", 4),
        ]
        now = datetime.now(timezone.utc).isoformat()
        conn.executemany(
            """INSERT INTO projects
               (title,description,tags,image_url,github_url,live_url,sort_order,created_at)
               VALUES (?,?,?,?,?,?,?,?)""",
            [(a,b,c,d,e,f,g,now) for a,b,c,d,e,f,g in seeds]
        )
    conn.commit()
    conn.close()


def supabase_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }


def sb_request(method, table, **kwargs):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    params = kwargs.pop("params", {})
    headers = supabase_headers()
    headers["Prefer"] = kwargs.pop("prefer", "return=representation")
    response = requests.request(
        method, url, headers=headers, params=params, timeout=12, **kwargs
    )
    response.raise_for_status()
    if not response.text:
        return []
    return response.json()


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def get_messages():
    if using_supabase():
        return sb_request(
            "GET", "messages",
            params={"select": "*", "order": "received_at.desc"}
        )
    conn = db_connect()
    rows = [dict(r) for r in conn.execute(
        "SELECT * FROM messages ORDER BY received_at DESC"
    ).fetchall()]
    conn.close()
    return rows


def get_message(message_id):
    if using_supabase():
        rows = sb_request("GET", "messages",
                          params={"select": "*", "id": f"eq.{message_id}"})
        return rows[0] if rows else None
    conn = db_connect()
    row = conn.execute("SELECT * FROM messages WHERE id=?", (message_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def create_message(data):
    payload = {
        "name": data["name"],
        "email": data["email"],
        "subject": data.get("subject", ""),
        "message": data["message"],
        "received_at": now_iso(),
        "is_read": False,
    }
    if using_supabase():
        return sb_request("POST", "messages", json=payload)[0]
    conn = db_connect()
    cur = conn.execute(
        """INSERT INTO messages
           (name,email,subject,message,received_at,is_read)
           VALUES (?,?,?,?,?,0)""",
        (payload["name"], payload["email"], payload["subject"],
         payload["message"], payload["received_at"])
    )
    conn.commit()
    item = get_message(cur.lastrowid)
    conn.close()
    return item


def update_message(message_id, data):
    payload = {
        "name": data["name"],
        "email": data["email"],
        "subject": data.get("subject", ""),
        "message": data["message"],
        "is_read": bool(data.get("is_read", False)),
    }
    if using_supabase():
        rows = sb_request("PATCH", "messages", json=payload,
                          params={"id": f"eq.{message_id}"})
        return rows[0] if rows else None
    conn = db_connect()
    conn.execute(
        """UPDATE messages SET name=?, email=?, subject=?, message=?, is_read=?
           WHERE id=?""",
        (payload["name"], payload["email"], payload["subject"],
         payload["message"], int(payload["is_read"]), message_id)
    )
    conn.commit()
    conn.close()
    return get_message(message_id)


def delete_message(message_id):
    if using_supabase():
        sb_request("DELETE", "messages", params={"id": f"eq.{message_id}"})
        return
    conn = db_connect()
    conn.execute("DELETE FROM messages WHERE id=?", (message_id,))
    conn.commit()
    conn.close()


def mark_message_read(message_id, value=True):
    if using_supabase():
        sb_request("PATCH", "messages", json={"is_read": value},
                   params={"id": f"eq.{message_id}"})
        return
    conn = db_connect()
    conn.execute("UPDATE messages SET is_read=? WHERE id=?",
                 (int(value), message_id))
    conn.commit()
    conn.close()


def get_projects():
    if using_supabase():
        return sb_request(
            "GET", "projects",
            params={"select": "*", "order": "sort_order.asc,id.asc"}
        )
    conn = db_connect()
    rows = [dict(r) for r in conn.execute(
        "SELECT * FROM projects ORDER BY sort_order ASC, id ASC"
    ).fetchall()]
    conn.close()
    return rows


def get_project(project_id):
    if using_supabase():
        rows = sb_request("GET", "projects",
                          params={"select": "*", "id": f"eq.{project_id}"})
        return rows[0] if rows else None
    conn = db_connect()
    row = conn.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def create_project(data):
    payload = {
        "title": data["title"],
        "description": data["description"],
        "tags": data.get("tags", ""),
        "image_url": data.get("image_url", ""),
        "github_url": data.get("github_url", ""),
        "live_url": data.get("live_url", ""),
        "sort_order": int(data.get("sort_order", 0) or 0),
        "created_at": now_iso(),
    }
    if using_supabase():
        return sb_request("POST", "projects", json=payload)[0]
    conn = db_connect()
    cur = conn.execute(
        """INSERT INTO projects
           (title,description,tags,image_url,github_url,live_url,sort_order,created_at)
           VALUES (?,?,?,?,?,?,?,?)""",
        tuple(payload.values())
    )
    conn.commit()
    item = get_project(cur.lastrowid)
    conn.close()
    return item


def update_project(project_id, data):
    payload = {
        "title": data["title"],
        "description": data["description"],
        "tags": data.get("tags", ""),
        "image_url": data.get("image_url", ""),
        "github_url": data.get("github_url", ""),
        "live_url": data.get("live_url", ""),
        "sort_order": int(data.get("sort_order", 0) or 0),
    }
    if using_supabase():
        rows = sb_request("PATCH", "projects", json=payload,
                          params={"id": f"eq.{project_id}"})
        return rows[0] if rows else None
    conn = db_connect()
    conn.execute(
        """UPDATE projects SET title=?, description=?, tags=?, image_url=?,
           github_url=?, live_url=?, sort_order=? WHERE id=?""",
        (*payload.values(), project_id)
    )
    conn.commit()
    conn.close()
    return get_project(project_id)


def delete_project(project_id):
    if using_supabase():
        sb_request("DELETE", "projects", params={"id": f"eq.{project_id}"})
        return
    conn = db_connect()
    conn.execute("DELETE FROM projects WHERE id=?", (project_id,))
    conn.commit()
    conn.close()


# -----------------------------
# Security / admin helpers
# -----------------------------
def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return session["csrf_token"]


def validate_csrf():
    token = request.form.get("_csrf", "")
    return secrets.compare_digest(token, session.get("csrf_token", ""))


@app.context_processor
def inject_globals():
    return {"csrf_token": csrf_token()}


# -----------------------------
# Public routes
# -----------------------------
@app.route("/")
def index():
    return render_template("index.html", projects=get_projects())


@app.route("/download-cv")
def download_cv():
    return send_from_directory(CV_FOLDER, "cv offical.pdf", as_attachment=True)


@app.route("/contact", methods=["POST"])
def contact():
    data = request.get_json(silent=True) or request.form.to_dict()

    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    subject = (data.get("subject") or "").strip()
    message = (data.get("message") or "").strip()

    if not name or not email or not message:
        return jsonify({"ok": False, "error": "Name, email and message are required."}), 400

    if len(name) > 100 or len(email) > 255 or len(subject) > 200 or len(message) > 2000:
        return jsonify({"ok": False, "error": "One or more fields exceed the maximum allowed length."}), 400

    try:
        create_message({
            "name": name, "email": email,
            "subject": subject, "message": message
        })
        return jsonify({"ok": True, "message": "Thank you! Your message has been received."})
    except Exception as exc:
        app.logger.exception("Contact submission failed")
        return jsonify({"ok": False, "error": "Message could not be saved right now. Please try again."}), 500


# -----------------------------
# Admin routes
# -----------------------------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("admin_logged_in"):
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        if not validate_csrf():
            flash("Security check failed. Please try again.", "error")
            return redirect(url_for("admin_login"))

        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

        if not ADMIN_PASSWORD:
            flash("Admin password is not configured. Add ADMIN_PASSWORD to your .env file.", "error")
        elif secrets.compare_digest(username, ADMIN_USERNAME) and secrets.compare_digest(password, ADMIN_PASSWORD):
            session.clear()
            session["admin_logged_in"] = True
            session["admin_username"] = username
            session["csrf_token"] = secrets.token_urlsafe(32)
            next_url = request.args.get("next") or url_for("admin_dashboard")
            if not next_url.startswith("/"):
                next_url = url_for("admin_dashboard")
            return redirect(next_url)
        else:
            flash("Invalid username or password.", "error")

    return render_template("admin/login.html")


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


@app.route("/admin")
@admin_required
def admin_dashboard():
    messages = get_messages()
    projects = get_projects()
    unread = sum(1 for m in messages if not m.get("is_read"))
    return render_template(
        "admin/dashboard.html",
        messages=messages,
        projects=projects,
        unread=unread,
    )


@app.route("/admin/messages")
@admin_required
def admin_messages():
    return render_template("admin/messages.html", messages=get_messages())


@app.route("/admin/messages/new", methods=["GET", "POST"])
@admin_required
def admin_message_new():
    if request.method == "POST":
        if not validate_csrf():
            flash("Security check failed.", "error")
            return redirect(url_for("admin_message_new"))
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        message = request.form.get("message", "").strip()
        if not name or not email or not message:
            flash("Name, email and message are required.", "error")
        else:
            create_message({
                "name": name, "email": email,
                "subject": request.form.get("subject", "").strip(),
                "message": message
            })
            flash("Message added.", "success")
            return redirect(url_for("admin_messages"))
    return render_template("admin/message_form.html", message=None, title="Add Message")


@app.route("/admin/messages/<int:message_id>/edit", methods=["GET", "POST"])
@admin_required
def admin_message_edit(message_id):
    message = get_message(message_id)
    if not message:
        return "Message not found", 404
    if request.method == "POST":
        if not validate_csrf():
            flash("Security check failed.", "error")
            return redirect(url_for("admin_message_edit", message_id=message_id))
        update_message(message_id, {
            "name": request.form.get("name", "").strip(),
            "email": request.form.get("email", "").strip(),
            "subject": request.form.get("subject", "").strip(),
            "message": request.form.get("message", "").strip(),
            "is_read": request.form.get("is_read") == "1",
        })
        flash("Message updated.", "success")
        return redirect(url_for("admin_messages"))
    return render_template("admin/message_form.html", message=message, title="Edit Message")


@app.post("/admin/messages/<int:message_id>/read")
@admin_required
def admin_message_read(message_id):
    if not validate_csrf():
        flash("Security check failed.", "error")
        return redirect(url_for("admin_messages"))
    mark_message_read(message_id, True)
    flash("Message marked as read.", "success")
    return redirect(url_for("admin_messages"))


@app.post("/admin/messages/<int:message_id>/delete")
@admin_required
def admin_message_delete(message_id):
    if not validate_csrf():
        flash("Security check failed.", "error")
        return redirect(url_for("admin_messages"))
    delete_message(message_id)
    flash("Message deleted.", "success")
    return redirect(url_for("admin_messages"))


@app.route("/admin/projects")
@admin_required
def admin_projects():
    return render_template("admin/projects.html", projects=get_projects())


@app.route("/admin/projects/new", methods=["GET", "POST"])
@admin_required
def admin_project_new():
    if request.method == "POST":
        if not validate_csrf():
            flash("Security check failed.", "error")
            return redirect(url_for("admin_project_new"))
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        if not title or not description:
            flash("Title and description are required.", "error")
        else:
            create_project(request.form)
            flash("Project added.", "success")
            return redirect(url_for("admin_projects"))
    return render_template("admin/project_form.html", project=None, title="Add Project")


@app.route("/admin/projects/<int:project_id>/edit", methods=["GET", "POST"])
@admin_required
def admin_project_edit(project_id):
    project = get_project(project_id)
    if not project:
        return "Project not found", 404
    if request.method == "POST":
        if not validate_csrf():
            flash("Security check failed.", "error")
            return redirect(url_for("admin_project_edit", project_id=project_id))
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        if not title or not description:
            flash("Title and description are required.", "error")
        else:
            update_project(project_id, request.form)
            flash("Project updated.", "success")
            return redirect(url_for("admin_projects"))
    return render_template("admin/project_form.html", project=project, title="Edit Project")


@app.post("/admin/projects/<int:project_id>/delete")
@admin_required
def admin_project_delete(project_id):
    if not validate_csrf():
        flash("Security check failed.", "error")
        return redirect(url_for("admin_projects"))
    delete_project(project_id)
    flash("Project deleted.", "success")
    return redirect(url_for("admin_projects"))


# Local initialization only. On Vercel, use Supabase.
if not using_supabase():
    init_sqlite()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)