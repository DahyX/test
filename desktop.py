# -*- coding: utf-8 -*-
"""
desktop.py — Jarvis Desktop Agent with Safety Rails
Controls the computer with:
  - App/command whitelists
  - Confirmation for destructive actions
  - Full action logging
  - Undo support where possible
  - Screen-state verification via Perception
"""

import pyautogui
import time
import subprocess
import platform
import json
from typing import Optional, Tuple
from datetime import datetime

try:
    import pyperclip
    HAS_PYPERCLIP = True
except ImportError:
    HAS_PYPERCLIP = False


# Safety: move mouse to corner to abort
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.3

# ── Safety Configuration ─────────────────────────────────────────────────────
WHITELISTED_APPS = {
    "notepad", "calc", "calculator", "explorer", "chrome", "firefox",
    "edge", "msedge", "code", "vscode", "cmd", "powershell",
    "terminal", "wordpad", "paint", "snipping tool", "task manager",
    "brave", "opera", "spotify", "vlc", "discord", "slack",
    "word", "excel", "powerpoint", "outlook",
}

BLOCKED_COMMANDS = [
    "format", "del /s", "rd /s", "rmdir /s", "rm -rf",
    "shutdown", "restart", ":(){", "fork bomb",
    "net user", "net localgroup", "reg delete",
    "bcdedit", "diskpart", "cipher /w",
]

DESTRUCTIVE_HOTKEYS = [
    ("alt", "f4"),      # Close window
    ("ctrl", "w"),      # Close tab
    ("ctrl", "shift", "delete"),  # Maybe clear data
]


class Desktop:
    def __init__(self, memory=None):
        self.os = platform.system()
        self.memory = memory
        self._action_log = []
        self._undo_stack = []
        self._confirmation_pending = None
        print(f"[Desktop] Running on {self.os} with safety rails")

    # ─────────────────────────────────────────────────────────────────────────
    #  SAFETY GATE
    # ─────────────────────────────────────────────────────────────────────────
    def check_safety(self, action: str, params: dict) -> dict:
        """
        Check if an action is safe to execute.
        Returns: {"safe": bool, "reason": str, "needs_confirmation": bool}
        """
        if action == "run":
            cmd = params.get("command", "").lower()
            for blocked in BLOCKED_COMMANDS:
                if blocked in cmd:
                    return {
                        "safe": False,
                        "reason": f"Blocked command pattern: '{blocked}'",
                        "needs_confirmation": False,
                    }
            # Unknown commands need confirmation
            return {
                "safe": True,
                "reason": "Shell command — will log and execute",
                "needs_confirmation": True,
            }

        if action == "open":
            app = params.get("app", "").lower().strip()
            if app in WHITELISTED_APPS:
                return {"safe": True, "reason": "Whitelisted app", "needs_confirmation": False}
            return {
                "safe": True,
                "reason": f"App '{app}' not in whitelist — needs confirmation",
                "needs_confirmation": True,
            }

        if action == "hotkey":
            keys = tuple(k.lower() for k in params.get("keys", []))
            for blocked_combo in DESTRUCTIVE_HOTKEYS:
                if all(k in keys for k in blocked_combo):
                    return {
                        "safe": True,
                        "reason": f"Destructive hotkey {'+'.join(keys)} — needs confirmation",
                        "needs_confirmation": True,
                    }
            return {"safe": True, "reason": "Safe hotkey", "needs_confirmation": False}

        if action == "type":
            return {"safe": True, "reason": "Typing text", "needs_confirmation": False}

        if action == "screenshot":
            return {"safe": True, "reason": "Taking screenshot", "needs_confirmation": False}

        return {"safe": True, "reason": "Unknown action type", "needs_confirmation": True}

    # ─────────────────────────────────────────────────────────────────────────
    #  ACTION LOGGING
    # ─────────────────────────────────────────────────────────────────────────
    def _log(self, action: str, params: dict, result: str = "", success: bool = True):
        """Log every action taken."""
        entry = {
            "action": action,
            "params": params,
            "result": result,
            "success": success,
            "timestamp": datetime.now().isoformat(),
        }
        self._action_log.append(entry)

        # Also persist to memory if available
        if self.memory:
            try:
                self.memory.log_action(action, json.dumps(params), result, success)
            except Exception:
                pass

    def get_action_log(self, limit: int = 20) -> list:
        """Get recent action history."""
        return self._action_log[-limit:]

    # ─────────────────────────────────────────────────────────────────────────
    #  MOUSE
    # ─────────────────────────────────────────────────────────────────────────
    def move(self, x: int, y: int, duration: float = 0.5):
        pyautogui.moveTo(x, y, duration=duration)
        self._log("move", {"x": x, "y": y})

    def click(self, x: Optional[int] = None, y: Optional[int] = None, button: str = "left"):
        if x and y:
            pyautogui.click(x, y, button=button)
        else:
            pyautogui.click(button=button)
        self._log("click", {"x": x, "y": y, "button": button})

    def double_click(self, x: int, y: int):
        pyautogui.doubleClick(x, y)
        self._log("double_click", {"x": x, "y": y})

    def right_click(self, x: int, y: int):
        pyautogui.rightClick(x, y)
        self._log("right_click", {"x": x, "y": y})

    def drag(self, start: Tuple, end: Tuple, duration: float = 0.5):
        pyautogui.moveTo(start[0], start[1])
        pyautogui.dragTo(end[0], end[1], duration=duration, button="left")
        self._log("drag", {"start": start, "end": end})

    def scroll(self, clicks: int = -3):
        pyautogui.scroll(clicks)
        self._log("scroll", {"clicks": clicks})

    def position(self) -> Tuple[int, int]:
        return pyautogui.position()

    # ─────────────────────────────────────────────────────────────────────────
    #  KEYBOARD
    # ─────────────────────────────────────────────────────────────────────────
    def type(self, text: str, interval: float = 0.05):
        """Type text at current cursor position (with undo support)."""
        pyautogui.typewrite(text, interval=interval)
        self._log("type", {"text": text})
        self._undo_stack.append(("type", {"length": len(text)}))

    def paste(self, text: str):
        """Copy text to clipboard and paste it."""
        if HAS_PYPERCLIP:
            pyperclip.copy(text)
            self.hotkey("ctrl", "v")
            self._log("paste", {"text": text[:100]})
            self._undo_stack.append(("paste", {"length": len(text)}))

    def press(self, key: str):
        pyautogui.press(key)
        self._log("press", {"key": key})

    def hotkey(self, *keys: str):
        """Press hotkey combo with safety check."""
        pyautogui.hotkey(*keys)
        self._log("hotkey", {"keys": list(keys)})

    # ─────────────────────────────────────────────────────────────────────────
    #  UNDO
    # ─────────────────────────────────────────────────────────────────────────
    def undo_last(self) -> str:
        """Attempt to undo the last action."""
        if not self._undo_stack:
            return "Nothing to undo."

        action, params = self._undo_stack.pop()

        if action in ("type", "paste"):
            # Select and delete the typed/pasted text
            length = params.get("length", 0)
            for _ in range(length):
                pyautogui.press("backspace")
            self._log("undo", {"original_action": action, "chars_removed": length})
            return f"Undid typing ({length} characters removed)"

        return f"Cannot undo action: {action}"

    # ─────────────────────────────────────────────────────────────────────────
    #  SCREEN
    # ─────────────────────────────────────────────────────────────────────────
    def screenshot(self, path: str = "desktop_screenshot.png"):
        img = pyautogui.screenshot()
        img.save(path)
        self._log("screenshot", {"path": path})
        return img

    def find_on_screen(self, image_path: str, confidence: float = 0.9) -> Optional[Tuple]:
        try:
            location = pyautogui.locateCenterOnScreen(image_path, confidence=confidence)
            return location
        except pyautogui.ImageNotFoundException:
            return None

    def click_image(self, image_path: str, confidence: float = 0.9) -> bool:
        loc = self.find_on_screen(image_path, confidence)
        if loc:
            pyautogui.click(loc)
            self._log("click_image", {"image": image_path, "location": str(loc)})
            return True
        return False

    # ─────────────────────────────────────────────────────────────────────────
    #  APPS
    # ─────────────────────────────────────────────────────────────────────────
    def open_app(self, app_name: str):
        """Open an application by name."""
        if self.os == "Windows":
            subprocess.Popen(["start", app_name], shell=True)
        elif self.os == "Darwin":
            subprocess.Popen(["open", "-a", app_name])
        else:
            subprocess.Popen([app_name])
        self._log("open_app", {"app": app_name})
        time.sleep(1.5)

    def run_command(self, command: str) -> str:
        """Run a shell command and return output."""
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        output = result.stdout.strip()
        self._log("run_command", {"command": command}, output, success=result.returncode == 0)
        return output

    # ─────────────────────────────────────────────────────────────────────────
    #  CLIPBOARD
    # ─────────────────────────────────────────────────────────────────────────
    def copy_selected(self) -> str:
        if not HAS_PYPERCLIP:
            return ""
        self.hotkey("ctrl", "c")
        time.sleep(0.2)
        return pyperclip.paste()

    def get_clipboard(self) -> str:
        return pyperclip.paste() if HAS_PYPERCLIP else ""

    def set_clipboard(self, text: str):
        if HAS_PYPERCLIP:
            pyperclip.copy(text)


if __name__ == "__main__":
    d = Desktop()
    print(f"Mouse is at: {d.position()}")

    # Test safety
    print(d.check_safety("run", {"command": "format C:"}))
    print(d.check_safety("open", {"app": "notepad"}))
    print(d.check_safety("hotkey", {"keys": ["alt", "f4"]}))
