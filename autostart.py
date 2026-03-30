# -*- coding: utf-8 -*-
"""
autostart.py — Windows Startup Integration
Makes Jarvis start automatically when the user logs in.
Uses the Windows Startup folder via a .vbs silent launcher.
"""

import os
import sys


def get_startup_folder() -> str:
    """Get the Windows Startup folder path."""
    return os.path.join(
        os.environ.get("APPDATA", ""),
        "Microsoft", "Windows", "Start Menu", "Programs", "Startup"
    )


def get_project_root() -> str:
    """Get the Jarvis project root."""
    return os.path.dirname(os.path.abspath(__file__))


def install_autostart():
    """
    Install Jarvis to Windows Startup.
    Creates a VBScript wrapper that launches Jarvis silently in background.
    """
    startup_folder = get_startup_folder()
    project_root = get_project_root()
    python_exe = sys.executable
    jarvis_script = os.path.join(project_root, "jarvis.py")

    if not os.path.exists(startup_folder):
        print(f"[Autostart] Startup folder not found: {startup_folder}")
        return False

    # Create a batch file
    bat_path = os.path.join(project_root, "start_jarvis.bat")
    bat_content = f'''@echo off
cd /d "{project_root}"
"{python_exe}" "{jarvis_script}"
'''
    with open(bat_path, "w") as f:
        f.write(bat_content)

    # Create a VBScript to launch silently (no visible cmd window)
    vbs_path = os.path.join(startup_folder, "JarvisAutostart.vbs")
    vbs_content = f'''Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /c cd /d ""{project_root}"" && ""{python_exe}"" ""{jarvis_script}""", 0, False
Set WshShell = Nothing
'''

    try:
        with open(vbs_path, "w") as f:
            f.write(vbs_content)
        print(f"[Autostart] ✅ Installed to: {vbs_path}")
        print(f"[Autostart] Jarvis will start automatically on login.")
        print(f"[Autostart] Batch file: {bat_path}")
        return True
    except Exception as e:
        print(f"[Autostart] ❌ Failed: {e}")
        return False


def uninstall_autostart():
    """Remove Jarvis from Windows Startup."""
    startup_folder = get_startup_folder()
    vbs_path = os.path.join(startup_folder, "JarvisAutostart.vbs")
    bat_path = os.path.join(get_project_root(), "start_jarvis.bat")

    removed = False
    if os.path.exists(vbs_path):
        os.remove(vbs_path)
        print(f"[Autostart] Removed: {vbs_path}")
        removed = True
    if os.path.exists(bat_path):
        os.remove(bat_path)
        print(f"[Autostart] Removed: {bat_path}")
        removed = True

    if removed:
        print("[Autostart] ✅ Jarvis autostart disabled.")
    else:
        print("[Autostart] No autostart entries found.")
    return removed


def check_autostart() -> bool:
    """Check if Jarvis autostart is installed."""
    vbs_path = os.path.join(get_startup_folder(), "JarvisAutostart.vbs")
    return os.path.exists(vbs_path)


def status() -> str:
    """Get autostart status."""
    if check_autostart():
        vbs_path = os.path.join(get_startup_folder(), "JarvisAutostart.vbs")
        return f"✅ Autostart is ENABLED\n  Script: {vbs_path}"
    return "❌ Autostart is DISABLED\n  Run: python autostart.py install"


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Jarvis Autostart Manager")
    parser.add_argument("command", choices=["install", "uninstall", "status"],
                        help="Action to perform")
    args = parser.parse_args()

    if args.command == "install":
        install_autostart()
    elif args.command == "uninstall":
        uninstall_autostart()
    elif args.command == "status":
        print(status())
