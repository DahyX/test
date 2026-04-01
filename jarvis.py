# -*- coding: utf-8 -*-
"""
jarvis.py - CLI entrypoint for Jarvis.

start_jarvis.bat points here, so this file restores the missing executable path
and boots the same AgentLoop used by the web server.
"""

import sys

from core.main_loop import AgentLoop


def _print_banner(loop: AgentLoop) -> None:
    runtime = loop.get_runtime_status()
    print("=" * 60)
    print("JARVIS V6 - CLI")
    print(runtime["model_label"])
    print(
        "Inherited Claude assets: "
        f"{runtime['ecc_command_count']} commands, "
        f"{runtime['ecc_agent_count']} agents, "
        f"{runtime['cce_command_count']} Extended Source commands"
    )
    print("Try: /plan improve jarvis, /code-review core/main_loop.py, @architect redesign the runtime")
    print("Type 'exit' or 'quit' to leave.")
    print("=" * 60)


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    loop = AgentLoop()
    _print_banner(loop)

    while True:
        try:
            user_input = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            return 0

        if not user_input:
            continue

        if user_input.lower() in {"exit", "quit"}:
            print("Goodbye.")
            return 0

        response = loop.run_cycle(user_input)
        print(f"Jarvis> {response}\n")


if __name__ == "__main__":
    raise SystemExit(main())
