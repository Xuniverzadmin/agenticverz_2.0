#!/usr/bin/env python3
"""
Lightweight Flask Webhook Receiver for local development.

Features:
- SQLite storage (no external DB required)
- Simple web UI to view webhooks
- Auto-reload on changes
- Colorized terminal output

Usage:
    python app.py
    # Or with custom port
    PORT=5001 python app.py
"""

import json
import os
import sqlite3
from datetime import datetime, timezone
from flask import Flask, request, jsonify, render_template_string

# Configuration
DB_PATH = os.environ.get("WEBHOOK_DB", "/tmp/webhooks.db")
PORT = int(os.environ.get("PORT", "5000"))
HOST = os.environ.get("HOST", "0.0.0.0")

app = Flask(__name__)


# ========== Database ==========


def init_db():
    """Initialize SQLite database."""
    con = sqlite3.connect(DB_PATH)
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS webhooks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            received_at TEXT NOT NULL,
            method TEXT NOT NULL,
            path TEXT NOT NULL,
            content_type TEXT,
            headers TEXT,
            body TEXT,
            body_size INTEGER,
            source_ip TEXT,
            alertname TEXT,
            severity TEXT,
            status TEXT
        )
    """
    )
    con.execute(
        "CREATE INDEX IF NOT EXISTS idx_received_at ON webhooks(received_at DESC)"
    )
    con.execute("CREATE INDEX IF NOT EXISTS idx_alertname ON webhooks(alertname)")
    con.commit()
    con.close()


def save_webhook(data: dict) -> int:
    """Save webhook to database, return ID."""
    con = sqlite3.connect(DB_PATH)
    cur = con.execute(
        """
        INSERT INTO webhooks (
            received_at, method, path, content_type, headers,
            body, body_size, source_ip, alertname, severity, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            data["received_at"],
            data["method"],
            data["path"],
            data.get("content_type"),
            json.dumps(data.get("headers", {})),
            json.dumps(data.get("body")) if data.get("body") else None,
            data.get("body_size"),
            data.get("source_ip"),
            data.get("alertname"),
            data.get("severity"),
            data.get("status"),
        ),
    )
    webhook_id = cur.lastrowid
    con.commit()
    con.close()
    return webhook_id


def get_webhooks(limit: int = 100, alertname: str = None) -> list:
    """Get webhooks from database."""
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row

    query = "SELECT * FROM webhooks"
    params = []

    if alertname:
        query += " WHERE alertname = ?"
        params.append(alertname)

    query += " ORDER BY received_at DESC LIMIT ?"
    params.append(limit)

    cur = con.execute(query, params)
    rows = cur.fetchall()
    con.close()

    return [dict(row) for row in rows]


def get_webhook_by_id(webhook_id: int) -> dict:
    """Get a single webhook by ID."""
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.execute("SELECT * FROM webhooks WHERE id = ?", (webhook_id,))
    row = cur.fetchone()
    con.close()
    return dict(row) if row else None


# ========== Webhook Endpoints ==========


@app.route("/webhook", methods=["POST", "PUT", "GET", "HEAD"])
@app.route("/webhook/<path:subpath>", methods=["POST", "PUT", "GET", "HEAD"])
def receive_webhook(subpath: str = ""):
    """Receive and store a webhook."""
    path = f"/webhook/{subpath}" if subpath else "/webhook"

    # Parse body
    body = None
    content_type = request.headers.get("Content-Type", "")

    try:
        if "application/json" in content_type:
            body = request.get_json(force=False, silent=True)
        else:
            body = request.data.decode("utf-8", errors="replace")
    except Exception:
        body = request.data.decode("utf-8", errors="replace")

    # Extract alert fields
    alertname = None
    severity = None
    status = None

    if isinstance(body, list) and body:
        first = body[0]
        if isinstance(first, dict):
            labels = first.get("labels", {})
            alertname = labels.get("alertname")
            severity = labels.get("severity")
            status = first.get("status")
    elif isinstance(body, dict):
        labels = body.get("labels", {})
        alertname = labels.get("alertname")
        severity = labels.get("severity")
        status = body.get("status")

    # Save webhook
    webhook_data = {
        "received_at": datetime.now(timezone.utc).isoformat(),
        "method": request.method,
        "path": path,
        "content_type": content_type,
        "headers": dict(request.headers),
        "body": body,
        "body_size": len(request.data),
        "source_ip": request.remote_addr,
        "alertname": alertname,
        "severity": severity,
        "status": status,
    }

    webhook_id = save_webhook(webhook_data)

    # Console output with colors
    color = "\033[92m"  # Green
    if severity == "critical" or severity == "P1":
        color = "\033[91m"  # Red
    elif severity == "warning" or severity == "P2":
        color = "\033[93m"  # Yellow

    reset = "\033[0m"

    print(f"{color}[WEBHOOK #{webhook_id}]{reset} {request.method} {path}")
    print(f"  Content-Type: {content_type}")
    if alertname:
        print(f"  Alert: {alertname} ({severity or 'unknown'})")
    if body:
        body_preview = (
            json.dumps(body)[:200]
            if isinstance(body, (dict, list))
            else str(body)[:200]
        )
        print(f"  Body: {body_preview}...")
    print()

    return jsonify({"status": "ok", "id": webhook_id})


# ========== Query Endpoints ==========


@app.route("/webhooks")
def list_webhooks():
    """List webhooks as JSON."""
    limit = request.args.get("limit", 100, type=int)
    alertname = request.args.get("alertname")
    webhooks = get_webhooks(limit=limit, alertname=alertname)

    # Parse stored JSON strings
    for w in webhooks:
        if w.get("headers"):
            w["headers"] = json.loads(w["headers"])
        if w.get("body"):
            try:
                w["body"] = json.loads(w["body"])
            except (json.JSONDecodeError, TypeError):
                pass

    return jsonify(webhooks)


@app.route("/webhooks/<int:webhook_id>")
def get_webhook(webhook_id: int):
    """Get a specific webhook."""
    webhook = get_webhook_by_id(webhook_id)
    if not webhook:
        return jsonify({"error": "Not found"}), 404

    if webhook.get("headers"):
        webhook["headers"] = json.loads(webhook["headers"])
    if webhook.get("body"):
        try:
            webhook["body"] = json.loads(webhook["body"])
        except (json.JSONDecodeError, TypeError):
            pass

    return jsonify(webhook)


@app.route("/clear", methods=["POST", "DELETE"])
def clear_webhooks():
    """Clear all webhooks."""
    con = sqlite3.connect(DB_PATH)
    con.execute("DELETE FROM webhooks")
    con.commit()
    con.close()
    print("\033[93m[CLEARED] All webhooks deleted\033[0m")
    return jsonify({"status": "cleared"})


# ========== Web UI ==========


UI_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Webhook Receiver</title>
    <meta http-equiv="refresh" content="5">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 20px; background: #1a1a2e; color: #eee; }
        h1 { color: #00d4ff; }
        .webhook { background: #16213e; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #00d4ff; }
        .webhook.P1, .webhook.critical { border-left-color: #ff4444; }
        .webhook.P2, .webhook.warning { border-left-color: #ffaa00; }
        .webhook.P3 { border-left-color: #00ff88; }
        .meta { color: #888; font-size: 0.9em; margin-bottom: 8px; }
        .alertname { color: #00d4ff; font-weight: bold; }
        .severity { padding: 2px 8px; border-radius: 4px; font-size: 0.8em; }
        .severity.P1, .severity.critical { background: #ff4444; color: white; }
        .severity.P2, .severity.warning { background: #ffaa00; color: black; }
        .severity.P3 { background: #00ff88; color: black; }
        pre { background: #0f0f23; padding: 10px; border-radius: 4px; overflow-x: auto; font-size: 0.85em; }
        .stats { background: #16213e; padding: 10px 20px; border-radius: 8px; margin-bottom: 20px; display: inline-block; }
        .actions { margin-bottom: 20px; }
        .btn { padding: 8px 16px; background: #00d4ff; color: #1a1a2e; border: none; border-radius: 4px; cursor: pointer; margin-right: 10px; }
        .btn:hover { background: #00b4e0; }
        .btn.danger { background: #ff4444; color: white; }
        .btn.danger:hover { background: #dd3333; }
    </style>
</head>
<body>
    <h1>🎣 Webhook Receiver</h1>
    <div class="stats">
        <strong>{{ webhooks|length }}</strong> webhooks captured
        | Auto-refresh: 5s
        | <a href="/webhooks" style="color: #00d4ff;">JSON API</a>
    </div>
    <div class="actions">
        <button class="btn" onclick="location.reload()">Refresh</button>
        <button class="btn danger" onclick="clearWebhooks()">Clear All</button>
    </div>
    {% for w in webhooks %}
    <div class="webhook {{ w.severity or '' }}">
        <div class="meta">
            #{{ w.id }} | {{ w.received_at }} | {{ w.method }} {{ w.path }}
            {% if w.alertname %}<span class="alertname">{{ w.alertname }}</span>{% endif %}
            {% if w.severity %}<span class="severity {{ w.severity }}">{{ w.severity }}</span>{% endif %}
        </div>
        <pre>{{ w.body_pretty }}</pre>
    </div>
    {% endfor %}
    <script>
        function clearWebhooks() {
            if (confirm('Clear all webhooks?')) {
                fetch('/clear', {method: 'POST'}).then(() => location.reload());
            }
        }
    </script>
</body>
</html>
"""


@app.route("/")
def ui():
    """Simple web UI."""
    webhooks = get_webhooks(limit=50)

    for w in webhooks:
        if w.get("body"):
            try:
                body = json.loads(w["body"])
                w["body_pretty"] = json.dumps(body, indent=2)
            except (json.JSONDecodeError, TypeError):
                w["body_pretty"] = w["body"]
        else:
            w["body_pretty"] = "(empty)"

    return render_template_string(UI_TEMPLATE, webhooks=webhooks)


# ========== Health ==========


@app.route("/health")
def health():
    """Health check."""
    return jsonify({"status": "healthy", "db": DB_PATH})


# ========== Main ==========


if __name__ == "__main__":
    print("\033[96m")
    print("=" * 60)
    print(" 🎣 AOS Webhook Receiver (Dev Mode)")
    print("=" * 60)
    print("\033[0m")
    print(f"  Database: {DB_PATH}")
    print(f"  Endpoint: http://{HOST}:{PORT}/webhook")
    print(f"  Web UI:   http://{HOST}:{PORT}/")
    print(f"  API:      http://{HOST}:{PORT}/webhooks")
    print()
    print("  To expose via ngrok:")
    print(f"    ngrok http {PORT}")
    print()

    init_db()
    app.run(host=HOST, port=PORT, debug=True)
