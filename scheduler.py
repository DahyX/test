# -*- coding: utf-8 -*-
"""
scheduler.py — Jarvis Task Scheduler
Reminders, repeating tasks, and timed actions.
Uses APScheduler (pure Python, no dependencies on system cron).

Requirements (add to requirements.txt):
    APScheduler>=3.10.0
"""

import json
from datetime import datetime, timedelta
from typing import Callable, Optional

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.date import DateTrigger
    HAS_SCHEDULER = True
except ImportError:
    HAS_SCHEDULER = False


class TaskScheduler:
    """Manages scheduled reminders and recurring tasks."""

    def __init__(self, jarvis_run_fn: Callable, memory=None):
        self.run_fn = jarvis_run_fn
        self.memory = memory
        self._scheduler = None
        self._jobs = {}  # job_id → metadata

        if HAS_SCHEDULER:
            self._scheduler = BackgroundScheduler(timezone="UTC")
            self._scheduler.start()
            self._load_persisted_jobs()
            print("[Scheduler] Ready (APScheduler)")
        else:
            print("[Scheduler] APScheduler not installed — run: pip install APScheduler")

    # ── Public API ────────────────────────────────────────────────────────────

    def add_reminder(self, text: str, when: datetime, job_id: str = None) -> str:
        """Schedule a one-time reminder at a specific datetime."""
        if not HAS_SCHEDULER:
            return "Scheduler not available."
        job_id = job_id or f"remind_{int(when.timestamp())}"
        self._scheduler.add_job(
            func=self._fire_reminder,
            trigger=DateTrigger(run_date=when),
            id=job_id,
            args=[text],
            replace_existing=True,
        )
        self._jobs[job_id] = {"type": "reminder", "text": text, "when": when.isoformat()}
        self._persist_jobs()
        delta = when - datetime.utcnow()
        return f"Reminder set for {when.strftime('%Y-%m-%d %H:%M')} ({int(delta.total_seconds()/60)} min from now)"

    def add_recurring(self, task: str, cron_expr: str, job_id: str = None) -> str:
        """Add a recurring task using cron expression (e.g. '0 9 * * *' = 9am daily)."""
        if not HAS_SCHEDULER:
            return "Scheduler not available."
        job_id = job_id or f"cron_{hash(task) % 9999}"
        trigger = CronTrigger.from_crontab(cron_expr)
        self._scheduler.add_job(
            func=self._fire_task,
            trigger=trigger,
            id=job_id,
            args=[task],
            replace_existing=True,
        )
        self._jobs[job_id] = {"type": "cron", "task": task, "cron": cron_expr}
        self._persist_jobs()
        return f"Recurring task '{task}' scheduled (cron: {cron_expr})"

    def cancel(self, job_id: str) -> bool:
        """Cancel a scheduled job."""
        if not HAS_SCHEDULER:
            return False
        try:
            self._scheduler.remove_job(job_id)
            self._jobs.pop(job_id, None)
            self._persist_jobs()
            return True
        except Exception:
            return False

    def list_jobs(self) -> str:
        """Return a formatted list of all pending jobs."""
        if not self._jobs:
            return "No scheduled tasks."
        lines = ["Scheduled tasks:"]
        for jid, meta in self._jobs.items():
            if meta["type"] == "reminder":
                lines.append(f"  [{jid}] Reminder: '{meta['text']}' at {meta['when']}")
            else:
                lines.append(f"  [{jid}] Recurring: '{meta['task']}' (cron: {meta['cron']})")
        return "\n".join(lines)

    def stop(self):
        if self._scheduler and self._scheduler.running:
            self._scheduler.shutdown(wait=False)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _fire_reminder(self, text: str):
        print(f"\n[Reminder] {text}")
        try:
            self.run_fn(f"remind the user: {text}")
        except Exception as e:
            print(f"[Scheduler] Fire error: {e}")

    def _fire_task(self, task: str):
        print(f"\n[Scheduler] Running: {task}")
        try:
            self.run_fn(task)
        except Exception as e:
            print(f"[Scheduler] Task error: {e}")

    def _persist_jobs(self):
        if self.memory:
            try:
                self.memory.set_working("scheduler_jobs", json.dumps(self._jobs))
            except Exception:
                pass

    def _load_persisted_jobs(self):
        if not self.memory:
            return
        try:
            entry = self.memory.get_working("scheduler_jobs")
            if entry and entry.get("value"):
                jobs = json.loads(entry["value"])
                for job_id, meta in jobs.items():
                    if meta["type"] == "reminder":
                        when = datetime.fromisoformat(meta["when"])
                        if when > datetime.utcnow():
                            self.add_reminder(meta["text"], when, job_id=job_id)
                    elif meta["type"] == "cron":
                        self.add_recurring(meta["task"], meta["cron"], job_id=job_id)
                print(f"[Scheduler] Restored {len(jobs)} jobs")
        except Exception as e:
            print(f"[Scheduler] Load error: {e}")
