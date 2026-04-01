# -*- coding: utf-8 -*-
"""
web_server.py - Flask web server for Jarvis chat UI.
"""

import json
import os
import secrets
import threading
from functools import wraps

from flask import Flask, Response, abort, jsonify, render_template, request, stream_with_context

from core.main_loop import AgentLoop


class BrainInfo:
    def __init__(self, model: str):
        self.model = model


class EvaluatorInfo:
    def __init__(self, wrapper):
        self.wrapper = wrapper

    def run_benchmarks(self, **kwargs):
        return self.wrapper.loop.run_benchmark()

    def format_benchmark_report(self, results):
        return self.wrapper.loop.format_benchmark_report(results)


class SelfImproverInfo:
    def __init__(self, wrapper):
        self.wrapper = wrapper

    def self_check(self):
        return self.wrapper.loop.run_self_check()

    def format_self_check(self, results):
        return self.wrapper.loop.format_self_check(results)


class LearnerInfo:
    def __init__(self):
        self.running = False
        self.queue = []
        self._pages_learned = 0


class JarvisWrapper:
    def __init__(self):
        self.loop = AgentLoop()
        self.runtime_status = self.loop.get_runtime_status()
        self.brain = BrainInfo(self.runtime_status["model_label"])
        self.memory = self.loop.memory
        self.learner = LearnerInfo()
        self.evaluator = EvaluatorInfo(self)
        self.self_improver = SelfImproverInfo(self)

    def refresh_runtime_status(self):
        self.runtime_status = self.loop.get_runtime_status()
        self.brain.model = self.runtime_status["model_label"]

    def run(self, msg):
        response = self.loop.run_cycle(msg)
        self.refresh_runtime_status()
        return response


app = Flask(__name__, template_folder="templates", static_folder="static")

TOKEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jarvis_token.txt")


def _load_or_create_token() -> str:
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r", encoding="utf-8") as file:
            return file.read().strip()

    token = secrets.token_hex(24)
    with open(TOKEN_FILE, "w", encoding="utf-8") as file:
        file.write(token)
    print(f"[Auth] Token saved to {TOKEN_FILE}")
    return token


API_TOKEN = os.environ.get("JARVIS_TOKEN") or _load_or_create_token()


def _check_auth() -> bool:
    return True


def require_auth(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        if not _check_auth():
            abort(401)
        return func(*args, **kwargs)

    return decorated


jarvis_instance = None
jarvis_lock = threading.Lock()


def get_jarvis():
    global jarvis_instance
    if jarvis_instance is None:
        jarvis_instance = JarvisWrapper()
    return jarvis_instance


@app.route("/")
def index():
    return render_template("chat.html", token=API_TOKEN)


@app.route("/api/chat", methods=["POST"])
@require_auth
def chat():
    data = request.json or {}
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "Empty message"}), 400

    jarvis = get_jarvis()
    with jarvis_lock:
        try:
            response = jarvis.run(message)
        except Exception as exc:
            response = f"Error: {exc}"

    return jsonify({"response": response, "model": jarvis.brain.model or "offline"})


@app.route("/api/chat/stream", methods=["POST"])
@require_auth
def chat_stream():
    data = request.json or {}
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "Empty message"}), 400

    jarvis = get_jarvis()

    def generate():
        try:
            with jarvis_lock:
                response_text = jarvis.run(message)

            words = response_text.split(" ")
            for index, word in enumerate(words):
                chunk = word + (" " if index < len(words) - 1 else "")
                yield f"data: {json.dumps({'token': chunk, 'done': False})}\n\n"

            yield f"data: {json.dumps({'token': '', 'done': True})}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'error': str(exc), 'done': True})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.route("/api/status", methods=["GET"])
@require_auth
def status():
    jarvis = get_jarvis()
    jarvis.refresh_runtime_status()
    stats = jarvis.memory.stats()
    runtime = jarvis.runtime_status
    repo = runtime.get("repo", {})
    llm_lab = runtime.get("llm_lab", {})
    foundation = runtime.get("cognitive_foundation", {})

    return jsonify(
        {
            "model": jarvis.brain.model or "offline",
            "facts": stats.get("total_facts", 0),
            "chunks": stats.get("semantic_chunks", 0),
            "sources": stats.get("urls_visited", 0),
            "episodes": stats.get("episodes", 0),
            "procedures": stats.get("procedures", 0),
            "working_items": stats.get("working_items", 0),
            "profile_items": stats.get("profile_items", 0),
            "learner_running": jarvis.learner.running,
            "learner_queue": len(jarvis.learner.queue),
            "learner_learned": jarvis.learner._pages_learned,
            "claude_commands": runtime["ecc_command_count"],
            "claude_agents": runtime["ecc_agent_count"],
            "claude_extended_commands": runtime["cce_command_count"],
            "claude_extended_skills": runtime["cce_skill_count"],
            "claude_aliases": runtime["alias_count"],
            "chat_ready": runtime.get("chat_ready", False),
            "tool_count": runtime.get("tool_count", 0),
            "repo_files": repo.get("indexed_files", 0),
            "repo_python_files": repo.get("python_files", 0),
            "llm_lab_phase": llm_lab.get("phase", ""),
            "llm_lab_focus": llm_lab.get("focus", ""),
            "llm_lab_source": llm_lab.get("source_url", ""),
            "llm_lab_dataset_path": llm_lab.get("dataset_path", ""),
            "llm_lab_dataset_examples": llm_lab.get("dataset_examples", 0),
            "foundation_model_roles": foundation.get("model_roles", 0),
            "foundation_verifier_stages": foundation.get("verifier_stages", 0),
            "foundation_autonomy_jobs": foundation.get("autonomy_jobs", 0),
            "foundation_benchmark_tracks": foundation.get("benchmark_tracks", 0),
        }
    )


@app.route("/api/benchmark", methods=["POST"])
@require_auth
def benchmark():
    jarvis = get_jarvis()
    with jarvis_lock:
        results = jarvis.evaluator.run_benchmarks(brain=jarvis.brain)
        report = jarvis.evaluator.format_benchmark_report(results)
    return jsonify({"report": report, "results": results})


@app.route("/api/self-check", methods=["POST"])
@require_auth
def self_check():
    jarvis = get_jarvis()
    with jarvis_lock:
        results = jarvis.self_improver.self_check()
        report = jarvis.self_improver.format_self_check(results)
    return jsonify({"report": report, "results": results})


@app.route("/api/history", methods=["GET"])
@require_auth
def history():
    jarvis = get_jarvis()
    episodes = jarvis.memory.get_recent_episodes(limit=50)
    return jsonify({"episodes": episodes})


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  JARVIS V3 - Web Interface")
    print("  Open: http://localhost:5000")
    print("=" * 50)
    print(f"[Auth] API token: {API_TOKEN}")
    print(f"[Auth] Add header: X-Jarvis-Token: {API_TOKEN}")
    print()
    get_jarvis()
    app.run(host="0.0.0.0", port=5000, debug=False)
