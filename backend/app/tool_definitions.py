TOOL_DECLARATIONS = [
    {
        "name": "get_repository",
        "description": "Get basic metadata about the repository: name, description, default branch, and whether it is private. Useful for orientation only; it does not show any code.",
    },
    {
        "name": "list_directory",
        "description": "List the files and folders inside one directory of the repository. Use an empty path for the repository root. Useful for understanding project structure before choosing files to read.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path relative to the repo root, e.g. 'src/auth'. Empty string for the root.",
                }
            },
        },
    },
    {
        "name": "search_repository",
        "description": "Search file contents in the repository for a text term. Returns the paths of files that contain it, not the file contents. Useful for finding which files mention something, such as 'signup' or 'INSERT'.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The text to search for. Prefer short, specific terms.",
                }
            },
            "required": ["query"],
        },
    },
    {
        "name": "read_file",
        "description": "Read the full contents of one specific file. Use it once you know the exact path, for example from a search or directory listing.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "File path relative to the repo root, e.g. 'app/auth/signup.py'.",
                }
            },
            "required": ["path"],
        },
    },
]