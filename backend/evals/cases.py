REPO_OWNER = "ashrithanarne"
REPO_NAME = "sentinel-eval-target"

CASES = [
    {
        "name": "model_used",
        "question": "What type of model is being used?",
        "expected_keywords": ["gemini"],
        "expected_files": ["backend/app/llm.py"],
    },
    {
        "name": "cache_check",
        "question": "Where is the logic that checks whether a repository is already saved in the database before calling GitHub?",
        "expected_keywords": ["get_or_create_repository"],
        "expected_files": ["backend/app/repository_service.py"],
    },
    {
        "name": "step_limit",
        "question": "What happens when the agent uses all of its allowed investigation steps?",
        "expected_keywords": ["step_limit_reached"],
        "expected_files": ["backend/app/agent.py"],
    },
    {
        "name": "tool_errors",
        "question": "What happens when a tool call fails during an investigation?",
        "expected_keywords": ["execute_tool"],
        "expected_files": ["backend/app/agent_tools.py"],
    },
    {
        "name": "absent_feature",
        "question": "Where is Redis used for caching in this app?",
        "expected_keywords": [],
        "expected_files": [],
        "expect_absent": True,
    },
]