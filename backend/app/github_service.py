import os
import requests
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_API_BASE = "https://api.github.com"


def get_repository(owner: str, repo: str) -> dict:
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