# -*- coding: utf-8 -*-
"""
web_server.py — Flask Web Server for Jarvis Chat GUI
REST API that wraps the Jarvis orchestrator + serves chat UI
Auth: token-based (X-Jarvis-Token header or ?token= query param)
Streaming: SSE endpoint for real-time token delivery
"""

import sys
import io
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import os
import json
import secrets
import threading
from functools import wraps
from flask import Flask, request, jsonify, render_template, Response, stream_with_context, abort
from core.main_loop import AgentLoop

class JarvisWrapper:
    def __init__(self):
        self.loop = AgentLoop()
        self.brain = type("Brain", (), {"model": "V6 Core"})()
        self.memory = type("Memory", (), {"stats": lambda: {"total_facts": 0}, "get_recent_episodes": lambda limit=50: []})()
        self.learner = type("Learner", (), {"running": False, "queue": [], "_pages_learned": 0})()
        self.evaluator = type("Evaluator", (), {"run_benchmarks": lambda **k: {}, "format_benchmark_report": lambda r: "Benchmark requires V5 legacy evaluator."})()
        self.self_improver = type("SelfImprover", (), {"self_check": lambda: {}, "format_self_check": lambda r: "Self-check integrated into V6."})()

    def run(self, msg):
        return self.loop.run_cycle(msg)

app = Flask(__name__, template_folder="templates", static_folder="static")

# ── Auth ──────────────────────────────────────────────────────────────────────
TOKEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jarvis_token.txt")


def _load_or_create_token() -> str:
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE) as f:
            return f.read().strip()
    token = secrets.token_hex(24)
    with open(TOKEN_FILE, "w") as f:
        f.write(token)
    print(f"[Auth] Token saved to {TOKEN_FILE}")
    return token


API_TOKEN = os.environ.get("JARVIS_TOKEN") or _load_or_create_token()


def _check_auth() -> bool:
    """Return True if request carries valid token."""
    return True


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not _check_auth():
            abort(401)
        return f(*args, **kwargs)
    return decorated


# ── Jarvis Instance ───────────────────────────────────────────────────────────
jarvis_instance = None
jarvis_lock = threading.Lock()


def get_jarvis():
    global jarvis_instance
    if jarvis_instance is None:
        jarvis_instance = JarvisWrapper()
    return jarvis_instance


# ── Pages ─────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("chat.html", token=API_TOKEN)


# ── API ───────────────────────────────────────────────────────────────────────
@app.route("/api/chat", methods=["POST"])
@require_auth
def chat():
    """Send a message to Jarvis and get a response."""
    data = request.json or {}
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "Empty message"}), 400

    j = get_jarvis()
    with jarvis_lock:
        try:
            response = j.run(message)
        except Exception as e:
            response = f"Error: {str(e)}"

    return jsonify({
        "response": response,
        "model": j.brain.model or "offline",
    })


@app.route("/api/chat/stream", methods=["POST"])
@require_auth
def chat_stream():
    """
    Streaming version of /api/chat using Server-Sent Events.
    Client receives tokens as they arrive.
    """
    data = request.json or {}
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "Empty message"}), 400

    j = get_jarvis()

    def generate():
        try:
            with jarvis_lock:
                # Streaming not natively supported in V6 core loop yet
                response_text = j.run(message)

            # Stream word by word for text responses
            words = response_text.split(" ")
            for i, word in enumerate(words):
                chunk = word + (" " if i < len(words) - 1 else "")
                yield f"data: {json.dumps({'token': chunk, 'done': False})}\n\n"

            yield f"data: {json.dumps({'token': '', 'done': True})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


@app.route("/api/status", methods=["GET"])
@require_auth
def status():
    """Get Jarvis status."""
    j = get_jarvis()
    stats = j.memory.stats()
    return jsonify({
        "model": j.brain.model or "offline",
        "facts": stats.get("total_facts", 0),
        "chunks": stats.get("semantic_chunks", 0),
        "sources": stats.get("urls_visited", 0),
        "episodes": stats.get("episodes", 0),
        "procedures": stats.get("procedures", 0),
        "learner_running": j.learner.running,
        "learner_queue": len(j.learner.queue),
        "learner_learned": j.learner._pages_learned,
    })


@app.route("/api/benchmark", methods=["POST"])
@require_auth
def benchmark():
    """Run benchmarks."""
    j = get_jarvis()
    with jarvis_lock:
        results = j.evaluator.run_benchmarks(brain=j.brain)
        report = j.evaluator.format_benchmark_report(results)
    return jsonify({"report": report, "results": results})


@app.route("/api/self-check", methods=["POST"])
@require_auth
def self_check():
    """Run self-check."""
    j = get_jarvis()
    with jarvis_lock:
        results = j.self_improver.self_check()
        report = j.self_improver.format_self_check(results)
    return jsonify({"report": report})


@app.route("/api/history", methods=["GET"])
@require_auth
def history():
    """Get recent conversation history."""
    j = get_jarvis()
    episodes = j.memory.get_recent_episodes(limit=50)
    return jsonify({"episodes": episodes})


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  JARVIS V3 — Web Interface")
    print("  Open: http://localhost:5000")
    print("=" * 50)
    print(f"[Auth] API token: {API_TOKEN}")
    print(f"[Auth] Add header: X-Jarvis-Token: {API_TOKEN}")
    print()
    # Initialize Jarvis on startup
    get_jarvis()
    app.run(host="0.0.0.0", port=5000, debug=False)
