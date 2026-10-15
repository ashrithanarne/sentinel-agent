#This is the actual agent loop
from app import llm
from app.agent_tools import execute_tool
from app.tool_definitions import TOOL_DECLARATIONS

MAX_STEPS = 10

SYSTEM_PROMPT = """You are a software investigation agent examining the GitHub repository {owner}/{repo}.
Use the tools to gather evidence about the user's problem. Choose the most useful next step each time.
If a search returns nothing, browse with list_directory and read likely files instead.
Base your conclusions only on files you actually read. When you have enough evidence, stop calling tools and answer with:
1. Likely answer or root cause
2. Evidence (file paths and what you saw in them)
3. What remains uncertain"""


def _short(result: dict, limit: int = 100) -> str:
    text = str(result)
    return text if len(text) <= limit else text[:limit] + "..."


def investigate(owner: str, repo: str, problem: str) -> dict:
    system = SYSTEM_PROMPT.format(owner=owner, repo=repo)
    contents = [llm.user_message(problem)]

    for step in range(1, MAX_STEPS + 1):
        model_message = llm.generate(contents, system, TOOL_DECLARATIONS)
        contents.append(model_message)

        calls = llm.get_function_calls(model_message)
        if not calls:
            return {"status": "completed", "steps": step, "answer": llm.get_text(model_message)}

        results = []
        for call in calls:
            print(f"[step {step}] {call['name']}({call['args']})")
            result = execute_tool(call["name"], call["args"], owner, repo)
            print(f"          -> {_short(result)}")
            results.append((call["name"], result))
        contents.append(llm.tool_result_message(results))

    return {"status": "step_limit_reached", "steps": MAX_STEPS, "answer": None}