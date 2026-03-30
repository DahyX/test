# Example Jarvis plugin — simple calculator
PLUGIN_NAME = "calculator"
PLUGIN_DESCRIPTION = "Evaluate a math expression"
PLUGIN_ACTIONS = ["calculate"]

def handle(action, params, jarvis):
    expr = params.get("expression", "")
    try:
        # Safe eval — only allow numbers and basic operators
        import re
        if not re.match(r'^[\d\s\+\-\*\/\(\)\.\%\*\*]+$', expr):
            return "Invalid expression — only numbers and operators allowed."
        result = eval(expr)
        return f"{expr} = {result}"
    except Exception as e:
        return f"Calculation error: {e}"
