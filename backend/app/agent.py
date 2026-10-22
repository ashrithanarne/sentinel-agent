#This is the actual agent loop
from app import llm
from app.agent_tools import execute_tool
from app.tool_definitions import TOOL_DECLARATIONS

MAX_STEPS = 10

SYSTEM_PROMPT = """You are a software investigation agent examining the GitHub repository {owner}/{repo}.
Use the tools to gather evidence about the user's problem. Choose the most useful next step each time.
If a search returns nothing, browse with list_directory and read likely files instead.
search_repository depends on GitHub's code search index, which may be incomplete. An empty result does NOT mean the term is absent from the code. If two searches return nothing, stop searching and browse with list_directory and read likely files instead.
Do not claim nothing is uncertain unless you read the relevant files. In section 3, list any tool failures or empty searches.
Base your conclusions only on files you actually read. When you have enough evidence, stop calling tools and answer with:
1. Likely answer or root cause
2. Evidence (file paths and what you saw in them)
3. What remains uncertain"""


def _short(result: dict, limit: int = 100) -> str:
    text = str(result)
    return text if len(text) <= limit else text[:limit] + "..."

#Main loop with best effort condition added
def investigate(owner: str, repo: str, problem: str, on_step=None) -> dict:
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
            if on_step:
                on_step(step, call["name"], call["args"], result)
            results.append((call["name"], result))
        contents.append(llm.tool_result_message(results))

    contents.append(llm.user_message(
        "You have used all available investigation steps. Do not call any more tools. "
        "Using only what you have gathered so far, give your best answer in the same format, "
        "and say clearly in section 3 that the investigation was cut short and what you could not verify."
    ))
    final = llm.generate(contents, system, TOOL_DECLARATIONS, allow_tools=False)
    return {"status": "step_limit_reached", "steps": MAX_STEPS, "answer": llm.get_text(final) or None}