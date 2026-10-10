import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

#client plays the same role as the SQLAlchemy engine: it holds the key and knows where to send requests.
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL = "gemini-3.5-flash-lite"


def ask(prompt: str) -> str:
    response = client.models.generate_content(model=MODEL, contents=prompt)  #One req-res, no memory. Whatever goes in contents is everything the model knows.
    return response.text