#This file solely handles all the functions to the GitHub API
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
def _search_github_index(owner: str, repo: str, query: str) -> list[dict]:
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




TEXT_EXTENSIONS = (".py", ".js", ".ts", ".tsx", ".java", ".go", ".md", ".txt",
                   ".json", ".yml", ".yaml", ".toml", ".html", ".css", ".sql", ".sh")
MAX_FILE_SIZE = 100_000
MAX_FILES_SCANNED = 40


def get_repository_tree(owner: str, repo: str) -> list[dict]:
    branch = get_repository(owner, repo)["default_branch"]
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/git/trees/{branch}"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}

    response = requests.get(url, headers=headers, params={"recursive": "1"})
    response.raise_for_status()

    return response.json()["tree"]


def _search_by_scanning(owner: str, repo: str, query: str) -> list[dict]:
    needle = query.lower()
    files = [
        item for item in get_repository_tree(owner, repo)
        if item["type"] == "blob"
        and item["path"].lower().endswith(TEXT_EXTENSIONS)
        and item.get("size", 0) <= MAX_FILE_SIZE
    ]

    matches = []
    for item in files[:MAX_FILES_SCANNED]:
        path = item["path"]
        try:
            content = read_file(owner, repo, path)["content"]
        except Exception:
            continue
        if needle in path.lower() or needle in content.lower():
            matches.append({"path": path, "name": path.split("/")[-1]})
    return matches


def search_repository(owner: str, repo: str, query: str) -> list[dict]:
    results = _search_github_index(owner, repo, query)
    if results:
        return results
    return _search_by_scanning(owner, repo, query)