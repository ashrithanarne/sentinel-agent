#This is the file that (solely) contains all the functions that handles the gemini calls and request, response formatting
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types,errors
import time

load_dotenv()

#client plays the same role as the SQLAlchemy engine: it holds the key and knows where to send requests.
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL = "gemini-3.5-flash-lite"

RETRYABLE_CODES = {429, 500, 503}
MAX_ATTEMPTS = 4


def ask(prompt: str) -> str:
    response = client.models.generate_content(model=MODEL, contents=prompt)  #One req-res, no memory. Whatever goes in contents is everything the model knows.
    return response.text


#types is a module in the SDK containing typed Python classes for requests and responses, so you build settings as objects instead of raw dictionaries.

def ask_with_tools(prompt: str, system_instruction: str, declarations: list) -> dict:
    #GenerateContentConfig holds the settings for one request
    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        tools=[types.Tool(function_declarations=declarations)],
    )
    response = client.models.generate_content(
        model=MODEL, contents=prompt, config=config
    )
    part = response.candidates[0].content.parts[0]    #drills into the response
    if part.function_call:
        return {"tool": part.function_call.name, "args": dict(part.function_call.args)}
    return {"text": response.text}

#Takes in user message and returns a content object with role and part to append to history
def user_message(text: str):
    return types.Content(role="user", parts=[types.Part(text=text)])


#Takes in a list and creates a content object with role and parts with one or multiple part in it(One for each function call), to be appended to history
def tool_result_message(results: list):
    # results: list of (tool_name, result_dict) pairs
    parts = [
        types.Part.from_function_response(name=name, response=result)
        for name, result in results
    ]
    return types.Content(role="user", parts=parts)


#Calls the model and returns entire content the model gives, also exponential wait times in case the server is busy.
def generate(contents: list, system_instruction: str, declarations: list, allow_tools: bool = True):
    config_kwargs = dict(
        system_instruction=system_instruction,
        tools=[types.Tool(function_declarations=declarations)],
    )
    if not allow_tools: #if this was the case where step limit is exceeded and the model needs to give the best effort answer
        config_kwargs["tool_config"] = types.ToolConfig(
            function_calling_config=types.FunctionCallingConfig(mode="NONE")
        )
    config = types.GenerateContentConfig(**config_kwargs)

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            _throttle()
            response = client.models.generate_content(
                model=MODEL, contents=contents, config=config
            )
            return response.candidates[0].content
        except errors.APIError as e:
            if e.code not in RETRYABLE_CODES or attempt == MAX_ATTEMPTS:
                raise
            wait = 20 * attempt if e.code == 429 else 2 ** attempt
            print(f"[llm] Gemini returned {e.code}, retrying in {wait}s (attempt {attempt}/{MAX_ATTEMPTS})")
            time.sleep(wait)


#Takes in the .contnt returned by the model and sperates all the function calls and its args into a list, later to be given to execute
def get_function_calls(content) -> list:
    return [
        {"name": p.function_call.name, "args": dict(p.function_call.args or {})}
        for p in (content.parts or [])
        if p.function_call
    ]


#Takes in the .content returned by the model and returns a string with is the appended version of all the text in the response
def get_text(content) -> str:
    return "".join(p.text for p in (content.parts or []) if p.text)

#Adding throttle so that it does not exceed the models RPM
MIN_SECONDS_BETWEEN_CALLS = 0   # set to 0 for a normal run, and increase depending on your RPM otherwise
_last_call_time = 0.0


def _throttle():
    global _last_call_time
    wait = MIN_SECONDS_BETWEEN_CALLS - (time.perf_counter() - _last_call_time)
    if wait > 0:
        time.sleep(wait)
    _last_call_time = time.perf_counter()