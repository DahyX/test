import sys
sys.path.append("c:\\Users\\DELL\\OneDrive\\Desktop\\Test")

from core.main_loop import AgentLoop

try:
    print("Initializing Jarvis V6 Brain (Backed by Open-Model Router)...")
    agent = AgentLoop()
    print("Testing Decision Engine...")
    result = agent.run_cycle("Bake a cake.")
    print("Final Output:", result)
except Exception as e:
    import traceback
    traceback.print_exc()
