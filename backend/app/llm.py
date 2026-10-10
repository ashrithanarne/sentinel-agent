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