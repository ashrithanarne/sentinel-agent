#This is the file that (solely) contains all the functions that handles the gemini calls and request, response formatting
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

#client plays the same role as the SQLAlchemy engine: it holds the key and knows where to send requests.
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL = "gemini-3.5-flash-lite"


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


#Calls the model and returns entire content the model gives
def generate(contents: list, system_instruction: str, declarations: list):
    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        tools=[types.Tool(function_declarations=declarations)],
    )
    response = client.models.generate_content(
        model=MODEL, contents=contents, config=config
    )
    return response.candidates[0].content


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