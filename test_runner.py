# -*- coding: utf-8 -*-
"""
test_runner.py — Code Validation & Testing
Runs compile checks, smoke tests, pytest, and custom commands.
Used by the self-improvement engine to validate patches.
"""

import subprocess
import sys
import os
import time
from typing import Optional


class TestRunner:
    """Runs validation tests on the Jarvis codebase."""

    def __init__(self, project_root: str = None):
        self.project_root = project_root or os.getcwd()
        self.python = sys.executable

    # ─────────────────────────────────────────────────────────────────────────
    #  GENERIC COMMAND RUNNER
    # ─────────────────────────────────────────────────────────────────────────
    def run_command(self, command: str, timeout: int = 60) -> dict:
        """Run a shell command and capture results."""
        start = time.time()
        try:
            result = subprocess.run(
                command, shell=True,
                capture_output=True, text=True,
                timeout=timeout, cwd=self.project_root
            )
            duration = time.time() - start
            return {
                "success": result.returncode == 0,
                "exit_code": result.returncode,
                "stdout": result.stdout.strip()[-2000:],  # Cap output
                "stderr": result.stderr.strip()[-2000:],
                "duration": round(duration, 2),
                "command": command,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False, "exit_code": -1,
                "stdout": "", "stderr": f"Timeout after {timeout}s",
                "duration": timeout, "command": command,
            }
        except Exception as e:
            return {
                "success": False, "exit_code": -1,
                "stdout": "", "stderr": str(e),
                "duration": time.time() - start, "command": command,
            }

    # ─────────────────────────────────────────────────────────────────────────
    #  COMPILE CHECK
    # ─────────────────────────────────────────────────────────────────────────
    def run_py_compile(self, paths: list = None) -> dict:
        """Run py_compile on specified files or all .py files."""
        if not paths:
            paths = [f for f in os.listdir(self.project_root)
                     if f.endswith(".py") and not f.startswith("__")]

        results = []
        all_pass = True

        for path in paths:
            abs_path = os.path.join(self.project_root, path) if not os.path.isabs(path) else path
            if not os.path.exists(abs_path):
                results.append({"file": path, "pass": False, "error": "File not found"})
                all_pass = False
                continue

            cmd = f'"{self.python}" -m py_compile "{abs_path}"'
            r = self.run_command(cmd, timeout=10)

            passed = r["success"]
            results.append({
                "file": path,
                "pass": passed,
                "error": r["stderr"] if not passed else "",
            })
            if not passed:
                all_pass = False

        return {
            "success": all_pass,
            "total": len(results),
            "passed": sum(1 for r in results if r["pass"]),
            "failed": sum(1 for r in results if not r["pass"]),
            "details": results,
        }

    # ─────────────────────────────────────────────────────────────────────────
    #  SMOKE TEST
    # ─────────────────────────────────────────────────────────────────────────
    def run_smoke_test(self) -> dict:
        """Run basic import and initialization smoke test."""
        smoke_script = """
import sys
errors = []

# Test 1: Import all modules
modules = [
    'embeddings', 'memory', 'learner', 'retriever', 'planner',
    'perception', 'desktop', 'ai_brain', 'evaluator', 'scraper',
    'codebase_manager', 'patch_manager', 'test_runner',
]
for mod in modules:
    try:
        __import__(mod)
    except Exception as e:
        errors.append(f"Import {mod}: {e}")

# Test 2: Memory initialization
try:
    from memory import Memory
    m = Memory("_smoke_test.db")
    stats = m.stats()
    import os
    os.remove("_smoke_test.db")
except Exception as e:
    errors.append(f"Memory init: {e}")

# Test 3: Embeddings
try:
    from embeddings import EmbeddingEngine
    e = EmbeddingEngine()
    v = e.embed("test sentence")
    assert len(v) > 0, "Empty embedding vector"
except Exception as e:
    errors.append(f"Embeddings: {e}")

if errors:
    print("SMOKE TEST FAILED:")
    for err in errors:
        print(f"  - {err}")
    sys.exit(1)
else:
    print("SMOKE TEST PASSED: All modules OK")
    sys.exit(0)
"""
        # Write temp script
        script_path = os.path.join(self.project_root, "_smoke_test_script.py")
        try:
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(smoke_script)

            result = self.run_command(f'"{self.python}" "{script_path}"', timeout=30)

            return {
                "success": result["success"],
                "stdout": result["stdout"],
                "stderr": result["stderr"],
                "duration": result["duration"],
            }
        finally:
            if os.path.exists(script_path):
                os.remove(script_path)

    # ─────────────────────────────────────────────────────────────────────────
    #  PYTEST
    # ─────────────────────────────────────────────────────────────────────────
    def run_pytest(self, target: str = "") -> dict:
        """Run pytest if available."""
        cmd = f'"{self.python}" -m pytest {target} -v --tb=short 2>&1'
        return self.run_command(cmd, timeout=120)

    # ─────────────────────────────────────────────────────────────────────────
    #  SYNTAX CHECK (AST)
    # ─────────────────────────────────────────────────────────────────────────
    def check_syntax(self, code: str) -> dict:
        """Check Python code syntax without writing to disk."""
        try:
            import ast
            ast.parse(code)
            return {"valid": True, "error": None}
        except SyntaxError as e:
            return {"valid": False, "error": f"Line {e.lineno}: {e.msg}"}

    # ─────────────────────────────────────────────────────────────────────────
    #  FULL VALIDATION PIPELINE
    # ─────────────────────────────────────────────────────────────────────────
    def validate_patch(self, changed_files: list = None) -> dict:
        """
        Full validation pipeline for a patch:
        1. py_compile on changed files
        2. Smoke test
        3. Report
        """
        results = {
            "compile": None,
            "smoke": None,
            "overall_success": False,
        }

        # Step 1: Compile check
        compile_result = self.run_py_compile(changed_files)
        results["compile"] = compile_result
        if not compile_result["success"]:
            results["overall_success"] = False
            return results

        # Step 2: Smoke test
        smoke_result = self.run_smoke_test()
        results["smoke"] = smoke_result

        results["overall_success"] = compile_result["success"] and smoke_result["success"]
        return results

    def format_validation_report(self, results: dict) -> str:
        """Format validation results for display."""
        lines = ["Validation Results:"]

        compile_r = results.get("compile", {})
        if compile_r:
            status = "✅ PASS" if compile_r.get("success") else "❌ FAIL"
            lines.append(f"  Compile: {status} ({compile_r.get('passed', 0)}/{compile_r.get('total', 0)} files)")
            if not compile_r.get("success"):
                for d in compile_r.get("details", []):
                    if not d["pass"]:
                        lines.append(f"    ✗ {d['file']}: {d['error'][:100]}")

        smoke_r = results.get("smoke", {})
        if smoke_r:
            status = "✅ PASS" if smoke_r.get("success") else "❌ FAIL"
            lines.append(f"  Smoke test: {status}")
            if not smoke_r.get("success") and smoke_r.get("stderr"):
                lines.append(f"    {smoke_r['stderr'][:200]}")

        overall = "✅ ALL PASSED" if results.get("overall_success") else "❌ VALIDATION FAILED"
        lines.append(f"\n  Overall: {overall}")

        return "\n".join(lines)
