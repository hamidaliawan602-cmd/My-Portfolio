"""
Hamid Ali Awan Portfolio
Flask Portfolio + Protected Admin CMS

Database:
    Supabase PostgreSQL via REST API

Environment variables:
    SUPABASE_URL
    SUPABASE_KEY
    SECRET_KEY
    ADMIN_USERNAME
    ADMIN_PASSWORD

Local development:
    Uses the same Supabase database as production.

Vercel:
    Set the same environment variables in Vercel.
"""

import os
import secrets
from datetime import datetime, timezone
from functools import wraps

import requests
from dotenv import load_dotenv

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)


# ============================================================
# Environment
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(BASE_DIR, ".env")

load_dotenv(ENV_FILE, override=True)


# ============================================================
# Flask Application
# ============================================================

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "change-this-local-secret"
)

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("VERCEL") == "1"


# ============================================================
# Paths
# ============================================================

CV_FOLDER = os.path.join(
    BASE_DIR,
    "static",
    "cv"
)


# ============================================================
# Supabase Configuration
# ============================================================

SUPABASE_URL = os.environ.get(
    "SUPABASE_URL",
    ""
).rstrip("/")

SUPABASE_KEY = os.environ.get(
    "SUPABASE_KEY",
    ""
)


# ============================================================
# Admin Configuration
# ============================================================

ADMIN_USERNAME = os.environ.get(
    "ADMIN_USERNAME",
    "admin"
)

ADMIN_PASSWORD = os.environ.get(
    "ADMIN_PASSWORD",
    ""
)


# ============================================================
# Validate Configuration
# ============================================================

if not SUPABASE_URL:
    raise RuntimeError(
        "SUPABASE_URL is not configured. "
        "Add SUPABASE_URL to your .env file locally "
        "and to Vercel Environment Variables."
    )

if not SUPABASE_KEY:
    raise RuntimeError(
        "SUPABASE_KEY is not configured. "
        "Add SUPABASE_KEY to your .env file locally "
        "and to Vercel Environment Variables."
    )


# ============================================================
# Supabase Helpers
# ============================================================

def using_supabase():
    """
    Supabase is the only database used by this application.
    """
    return True


def supabase_headers():
    """
    Headers used for Supabase REST API requests.
    """

    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }


def sb_request(method, table, **kwargs):
    """
    Send a REST API request to a Supabase table.
    """

    url = f"{SUPABASE_URL}/rest/v1/{table}"

    params = kwargs.pop("params", {})

    headers = supabase_headers()

    headers["Prefer"] = kwargs.pop(
        "prefer",
        "return=representation"
    )

    response = requests.request(
        method,
        url,
        headers=headers,
        params=params,
        timeout=12,
        **kwargs,
    )

    response.raise_for_status()

    if not response.text:
        return []

    return response.json()


# ============================================================
# General Helpers
# ============================================================

def now_iso():
    """
    Return current UTC time in ISO format.
    """

    return datetime.now(timezone.utc).isoformat()


# ============================================================
# Messages
# ============================================================

def get_messages():
    """
    Get all messages, newest first.
    """

    return sb_request(
        "GET",
        "messages",
        params={
            "select": "*",
            "order": "received_at.desc",
        },
    )


def get_message(message_id):
    """
    Get one message by ID.
    """

    rows = sb_request(
        "GET",
        "messages",
        params={
            "select": "*",
            "id": f"eq.{message_id}",
        },
    )

    return rows[0] if rows else None


def create_message(data):
    """
    Create a new contact message.
    """

    payload = {
        "name": data["name"],
        "email": data["email"],
        "subject": data.get("subject", ""),
        "message": data["message"],
        "received_at": now_iso(),
        "is_read": False,
    }

    rows = sb_request(
        "POST",
        "messages",
        json=payload,
    )

    return rows[0] if rows else None


def update_message(message_id, data):
    """
    Update an existing message.
    """

    payload = {
        "name": data["name"],
        "email": data["email"],
        "subject": data.get("subject", ""),
        "message": data["message"],
        "is_read": bool(
            data.get("is_read", False)
        ),
    }

    rows = sb_request(
        "PATCH",
        "messages",
        json=payload,
        params={
            "id": f"eq.{message_id}"
        },
    )

    return rows[0] if rows else None


def delete_message(message_id):
    """
    Delete a message.
    """

    sb_request(
        "DELETE",
        "messages",
        params={
            "id": f"eq.{message_id}"
        },
        prefer="return=minimal",
    )


def mark_message_read(message_id, value=True):
    """
    Mark a message as read/unread.
    """

    sb_request(
        "PATCH",
        "messages",
        json={
            "is_read": bool(value)
        },
        params={
            "id": f"eq.{message_id}"
        },
        prefer="return=minimal",
    )


# ============================================================
# Projects
# ============================================================

def get_projects():
    """
    Get ALL portfolio projects.

    There is NO hard-coded project limit.

    Projects are sorted by:
        1. sort_order
        2. id
    """

    return sb_request(
        "GET",
        "projects",
        params={
            "select": "*",
            "order": "sort_order.asc,id.asc",
        },
    )


def get_project(project_id):
    """
    Get one project by ID.
    """

    rows = sb_request(
        "GET",
        "projects",
        params={
            "select": "*",
            "id": f"eq.{project_id}",
        },
    )

    return rows[0] if rows else None


def create_project(data):
    """
    Create a new portfolio project.
    """

    try:
        sort_order = int(
            data.get("sort_order", 0) or 0
        )
    except (TypeError, ValueError):
        sort_order = 0

    payload = {
        "title": data.get("title", "").strip(),
        "description": data.get("description", "").strip(),
        "tags": data.get("tags", "").strip(),
        "image_url": data.get("image_url", "").strip(),
        "github_url": data.get("github_url", "").strip(),
        "live_url": data.get("live_url", "").strip(),
        "sort_order": sort_order,
        "created_at": now_iso(),
    }

    rows = sb_request(
        "POST",
        "projects",
        json=payload,
    )

    return rows[0] if rows else None


def update_project(project_id, data):
    """
    Update an existing portfolio project.
    """

    try:
        sort_order = int(
            data.get("sort_order", 0) or 0
        )
    except (TypeError, ValueError):
        sort_order = 0

    payload = {
        "title": data.get("title", "").strip(),
        "description": data.get("description", "").strip(),
        "tags": data.get("tags", "").strip(),
        "image_url": data.get("image_url", "").strip(),
        "github_url": data.get("github_url", "").strip(),
        "live_url": data.get("live_url", "").strip(),
        "sort_order": sort_order,
    }

    rows = sb_request(
        "PATCH",
        "projects",
        json=payload,
        params={
            "id": f"eq.{project_id}"
        },
    )

    return rows[0] if rows else None


def delete_project(project_id):
    """
    Delete a portfolio project.
    """

    sb_request(
        "DELETE",
        "projects",
        params={
            "id": f"eq.{project_id}"
        },
        prefer="return=minimal",
    )


# ============================================================
# Security / Admin Helpers
# ============================================================

def admin_required(view):
    """
    Protect admin routes.
    """

    @wraps(view)
    def wrapped(*args, **kwargs):

        if not session.get("admin_logged_in"):
            return redirect(
                url_for(
                    "admin_login",
                    next=request.path
                )
            )

        return view(*args, **kwargs)

    return wrapped


def csrf_token():
    """
    Create or return a CSRF token.
    """

    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)

    return session["csrf_token"]


def validate_csrf():
    """
    Validate CSRF token.
    """

    token = request.form.get(
        "_csrf",
        ""
    )

    stored_token = session.get(
        "csrf_token",
        ""
    )

    if not token or not stored_token:
        return False

    return secrets.compare_digest(
        token,
        stored_token
    )


@app.context_processor
def inject_globals():
    """
    Make csrf_token available to all templates.
    """

    return {
        "csrf_token": csrf_token()
    }


# ============================================================
# Public Routes
# ============================================================

@app.route("/")
def index():
    """
    Portfolio home page.

    IMPORTANT:
    Projects are loaded directly from Supabase.
    Therefore, projects added/edited/deleted
    from the admin panel automatically appear here.
    """

    try:
        projects = get_projects()

    except Exception:
        app.logger.exception(
            "Could not load projects"
        )

        projects = []

    return render_template(
        "index.html",
        projects=projects
    )


@app.route("/download-cv")
def download_cv():
    """
    Download CV.
    """

    return send_from_directory(
        CV_FOLDER,
        "cv offical.pdf",
        as_attachment=True
    )


@app.route(
    "/contact",
    methods=["POST"]
)
def contact():
    """
    Receive contact form submissions.
    """

    data = (
        request.get_json(silent=True)
        or request.form.to_dict()
    )

    name = (
        data.get("name") or ""
    ).strip()

    email = (
        data.get("email") or ""
    ).strip()

    subject = (
        data.get("subject") or ""
    ).strip()

    message = (
        data.get("message") or ""
    ).strip()

    # Required fields
    if not name or not email or not message:

        return jsonify({
            "ok": False,
            "error": (
                "Name, email and message "
                "are required."
            )
        }), 400

    # Maximum lengths
    if (
        len(name) > 100
        or len(email) > 255
        or len(subject) > 200
        or len(message) > 2000
    ):

        return jsonify({
            "ok": False,
            "error": (
                "One or more fields exceed "
                "the maximum allowed length."
            )
        }), 400

    try:

        create_message({
            "name": name,
            "email": email,
            "subject": subject,
            "message": message,
        })

        return jsonify({
            "ok": True,
            "message": (
                "Thank you! Your message "
                "has been received."
            )
        })

    except Exception:

        app.logger.exception(
            "Contact submission failed"
        )

        return jsonify({
            "ok": False,
            "error": (
                "Message could not be saved "
                "right now. Please try again."
            )
        }), 500


# ============================================================
# Admin Login
# ============================================================

@app.route(
    "/admin/login",
    methods=["GET", "POST"]
)
def admin_login():

    if session.get("admin_logged_in"):

        return redirect(
            url_for("admin_dashboard")
        )

    if request.method == "POST":

        if not validate_csrf():

            flash(
                "Security check failed. "
                "Please try again.",
                "error"
            )

            return redirect(
                url_for("admin_login")
            )

        username = (
            request.form.get("username") or ""
        ).strip()

        password = (
            request.form.get("password") or ""
        )

        if not ADMIN_PASSWORD:

            flash(
                "Admin password is not configured. "
                "Add ADMIN_PASSWORD to your "
                "environment variables.",
                "error"
            )

        elif (
            secrets.compare_digest(
                username,
                ADMIN_USERNAME
            )
            and
            secrets.compare_digest(
                password,
                ADMIN_PASSWORD
            )
        ):

            session.clear()

            session["admin_logged_in"] = True
            session["admin_username"] = username
            session["csrf_token"] = (
                secrets.token_urlsafe(32)
            )

            next_url = (
                request.args.get("next")
                or url_for("admin_dashboard")
            )

            # Prevent external redirects
            if not next_url.startswith("/"):
                next_url = url_for(
                    "admin_dashboard"
                )

            return redirect(next_url)

        else:

            flash(
                "Invalid username or password.",
                "error"
            )

    return render_template(
        "admin/login.html"
    )


@app.route("/admin/logout")
def admin_logout():

    session.clear()

    return redirect(
        url_for("admin_login")
    )


# ============================================================
# Admin Dashboard
# ============================================================

@app.route("/admin")
@admin_required
def admin_dashboard():

    messages = get_messages()
    projects = get_projects()

    unread = sum(
        1
        for message in messages
        if not message.get("is_read")
    )

    return render_template(
        "admin/dashboard.html",
        messages=messages,
        projects=projects,
        unread=unread,
    )


# ============================================================
# Admin - Messages
# ============================================================

@app.route("/admin/messages")
@admin_required
def admin_messages():

    return render_template(
        "admin/messages.html",
        messages=get_messages()
    )


@app.route(
    "/admin/messages/new",
    methods=["GET", "POST"]
)
@admin_required
def admin_message_new():

    if request.method == "POST":

        if not validate_csrf():

            flash(
                "Security check failed.",
                "error"
            )

            return redirect(
                url_for("admin_message_new")
            )

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        subject = request.form.get(
            "subject",
            ""
        ).strip()

        message = request.form.get(
            "message",
            ""
        ).strip()

        if not name or not email or not message:

            flash(
                "Name, email and message are required.",
                "error"
            )

        else:

            try:

                create_message({
                    "name": name,
                    "email": email,
                    "subject": subject,
                    "message": message,
                })

                flash(
                    "Message added.",
                    "success"
                )

                return redirect(
                    url_for("admin_messages")
                )

            except Exception:

                app.logger.exception(
                    "Message creation failed"
                )

                flash(
                    "Message could not be added.",
                    "error"
                )

    return render_template(
        "admin/message_form.html",
        message=None,
        title="Add Message"
    )


@app.route(
    "/admin/messages/<int:message_id>/edit",
    methods=["GET", "POST"]
)
@admin_required
def admin_message_edit(message_id):

    message = get_message(message_id)

    if not message:
        return "Message not found", 404

    if request.method == "POST":

        if not validate_csrf():

            flash(
                "Security check failed.",
                "error"
            )

            return redirect(
                url_for(
                    "admin_message_edit",
                    message_id=message_id
                )
            )

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        subject = request.form.get(
            "subject",
            ""
        ).strip()

        message_text = request.form.get(
            "message",
            ""
        ).strip()

        if not name or not email or not message_text:

            flash(
                "Name, email and message are required.",
                "error"
            )

        else:

            try:

                update_message(
                    message_id,
                    {
                        "name": name,
                        "email": email,
                        "subject": subject,
                        "message": message_text,
                        "is_read": (
                            request.form.get(
                                "is_read"
                            ) == "1"
                        ),
                    }
                )

                flash(
                    "Message updated.",
                    "success"
                )

                return redirect(
                    url_for("admin_messages")
                )

            except Exception:

                app.logger.exception(
                    "Message update failed"
                )

                flash(
                    "Message could not be updated.",
                    "error"
                )

    return render_template(
        "admin/message_form.html",
        message=message,
        title="Edit Message"
    )


@app.post(
    "/admin/messages/<int:message_id>/read"
)
@admin_required
def admin_message_read(message_id):

    if not validate_csrf():

        flash(
            "Security check failed.",
            "error"
        )

        return redirect(
            url_for("admin_messages")
        )

    try:

        mark_message_read(
            message_id,
            True
        )

        flash(
            "Message marked as read.",
            "success"
        )

    except Exception:

        app.logger.exception(
            "Mark message as read failed"
        )

        flash(
            "Could not update message.",
            "error"
        )

    return redirect(
        url_for("admin_messages")
    )


@app.post(
    "/admin/messages/<int:message_id>/delete"
)
@admin_required
def admin_message_delete(message_id):

    if not validate_csrf():

        flash(
            "Security check failed.",
            "error"
        )

        return redirect(
            url_for("admin_messages")
        )

    try:

        delete_message(message_id)

        flash(
            "Message deleted.",
            "success"
        )

    except Exception:

        app.logger.exception(
            "Message deletion failed"
        )

        flash(
            "Message could not be deleted.",
            "error"
        )

    return redirect(
        url_for("admin_messages")
    )


# ============================================================
# Admin - Projects
# ============================================================

@app.route("/admin/projects")
@admin_required
def admin_projects():

    return render_template(
        "admin/projects.html",
        projects=get_projects()
    )


@app.route(
    "/admin/projects/new",
    methods=["GET", "POST"]
)
@admin_required
def admin_project_new():

    if request.method == "POST":

        if not validate_csrf():

            flash(
                "Security check failed.",
                "error"
            )

            return redirect(
                url_for("admin_project_new")
            )

        title = request.form.get(
            "title",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        if not title or not description:

            flash(
                "Title and description are required.",
                "error"
            )

        else:

            try:

                create_project(
                    request.form
                )

                flash(
                    "Project added successfully.",
                    "success"
                )

                return redirect(
                    url_for("admin_projects")
                )

            except Exception:

                app.logger.exception(
                    "Project creation failed"
                )

                flash(
                    "Project could not be added.",
                    "error"
                )

    return render_template(
        "admin/project_form.html",
        project=None,
        title="Add Project"
    )


@app.route(
    "/admin/projects/<int:project_id>/edit",
    methods=["GET", "POST"]
)
@admin_required
def admin_project_edit(project_id):

    project = get_project(project_id)

    if not project:
        return "Project not found", 404

    if request.method == "POST":

        if not validate_csrf():

            flash(
                "Security check failed.",
                "error"
            )

            return redirect(
                url_for(
                    "admin_project_edit",
                    project_id=project_id
                )
            )

        title = request.form.get(
            "title",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        if not title or not description:

            flash(
                "Title and description are required.",
                "error"
            )

        else:

            try:

                update_project(
                    project_id,
                    request.form
                )

                flash(
                    "Project updated successfully.",
                    "success"
                )

                return redirect(
                    url_for("admin_projects")
                )

            except Exception:

                app.logger.exception(
                    "Project update failed"
                )

                flash(
                    "Project could not be updated.",
                    "error"
                )

    return render_template(
        "admin/project_form.html",
        project=project,
        title="Edit Project"
    )


@app.post(
    "/admin/projects/<int:project_id>/delete"
)
@admin_required
def admin_project_delete(project_id):

    if not validate_csrf():

        flash(
            "Security check failed.",
            "error"
        )

        return redirect(
            url_for("admin_projects")
        )

    try:

        delete_project(project_id)

        flash(
            "Project deleted successfully.",
            "success"
        )

    except Exception:

        app.logger.exception(
            "Project deletion failed"
        )

        flash(
            "Project could not be deleted.",
            "error"
        )

    return redirect(
        url_for("admin_projects")
    )


# ============================================================
# Health Check
# ============================================================

@app.route("/health")
def health():

    try:

        get_projects()

        return jsonify({
            "status": "ok",
            "database": "supabase"
        })

    except Exception as exc:

        app.logger.exception(
            "Health check failed"
        )

        return jsonify({
            "status": "error",
            "database": "supabase",
            "error": str(exc)
        }), 500


# ============================================================
# Application Entry Point
# ============================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )