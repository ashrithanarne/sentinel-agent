#This is the actual agent loop
from app import llm
from app.agent_tools import execute_tool
from app.tool_definitions import TOOL_DECLARATIONS
import json
import time

MAX_STEPS = 10

SYSTEM_PROMPT = """You are a software investigation agent examining the GitHub repository {owner}/{repo}.
Use the tools to gather evidence about the user's problem. Choose the most useful next step each time.
Never repeat a tool call you have already made with the same arguments; its result is already in the conversation.
search_repository may be incomplete: it falls back to scanning only a limited number of text files, so an empty result does NOT prove a term is absent from the code. If two searches return nothing, stop searching and browse with list_directory and read likely files instead.
Base your conclusions only on files you actually read. When you have enough evidence, stop calling tools and answer with:
1. Likely answer or root cause
2. Evidence (file paths and what you saw in them)
3. What remains uncertain: list which files you read, any empty searches or failed tools, and what you could not check. If your conclusion is that something does not exist, phrase it as 'no evidence found in the files I checked'. Never write that nothing is uncertain."""


def _short(result: dict, limit: int = 100) -> str:
    text = str(result)
    return text if len(text) <= limit else text[:limit] + "..."

#Main loop with best effort condition added. Timeing checks and check for repeated function calls added.
def investigate(owner: str, repo: str, problem: str, on_step=None) -> dict:
    system = SYSTEM_PROMPT.format(owner=owner, repo=repo)
    contents = [llm.user_message(problem)]
    seen_calls = set()

    for step in range(1, MAX_STEPS + 1):
        t0 = time.perf_counter()
        model_message = llm.generate(contents, system, TOOL_DECLARATIONS)
        print(f"[step {step}] model call took {time.perf_counter() - t0:.1f}s")
        contents.append(model_message)

        calls = llm.get_function_calls(model_message)
        if not calls:
            return {"status": "completed", "steps": step, "answer": llm.get_text(model_message)}

        results = []
        for call in calls:
            print(f"[step {step}] {call['name']}({call['args']})")
            key = (call["name"], json.dumps(call["args"], sort_keys=True, default=str))
            if key in seen_calls:
                result = {"error": "You already made this exact call earlier in this investigation, and its result is in the conversation above. Do not repeat it. Try a different tool or arguments, or give your answer."}
            else:
                seen_calls.add(key)
                t1 = time.perf_counter()
                result = execute_tool(call["name"], call["args"], owner, repo)
                print(f"          tool took {time.perf_counter() - t1:.1f}s")
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