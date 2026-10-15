#This file is like a bridge between the tool request from the model to the real functions, with owner and repo fixed(TO make sure only the allowed repo is accessed) and errors turned into data.
from app import github_service


def execute_tool(name: str, args: dict, owner: str, repo: str) -> dict:
    try:
        if name == "get_repository":
            return {"result": github_service.get_repository(owner, repo)}
        if name == "list_directory":
            return {"result": github_service.list_directory(owner, repo, args.get("path", ""))}
        if name == "search_repository":
            return {"result": github_service.search_repository(owner, repo, args["query"])}
        if name == "read_file":
            return {"result": github_service.read_file(owner, repo, args["path"])}
        return {"error": f"Unknown tool: {name}"}
    except Exception as e:
        return {"error": str(e)}