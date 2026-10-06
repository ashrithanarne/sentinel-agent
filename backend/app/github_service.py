import os
import requests
from dotenv import load_dotenv
import base64

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_API_BASE = "https://api.github.com"


def get_repository(owner: str, repo: str) -> dict:   #->dict defines the return type
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    data = response.json()
    return {
        "name": data["name"],
        "full_name": data["full_name"],
        "description": data["description"],
        "default_branch": data["default_branch"],
        "private": data["private"],
    }


def read_file(owner: str, repo: str, path: str) -> dict:
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{path}"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    data = response.json()
    content = base64.b64decode(data["content"]).decode("utf-8") #The returned content is usually encoded, so we have to decodeit before displaying it

    return {
        "path": data["path"],
        "content": content,
        "size": data["size"],
    }

#This function searches an entire repo and returns a list of the paths of files that contain the text "query". query is a regular expression/text and not a command
#This basically is to find, "which files contain the word abc?"
def search_repository(owner: str, repo: str, query: str) -> list[dict]:
    url = f"{GITHUB_API_BASE}/search/code"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    params = {"q": f"{query} repo:{owner}/{repo}"}

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    data = response.json()
    return [
        {"path": item["path"], "name": item["name"]}
        #It returns an object with an item key instead of an array of items.
        for item in data.get("items", [])
    ]

def list_directory(owner: str, repo: str, path: str = "") -> list[dict]:
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{path}"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    data = response.json()
    return [
        {"name": item["name"], "path": item["path"], "type": item["type"]}
        #returns an array of items
        for item in data
    ]