from fastapi import FastAPI, HTTPException
from app.github_service import get_repository

app=FastAPI()

@app.get("/health")
def health():
    return {"status":"ok"}

@app.get("/repo/{owner}/{repo}")
def read_repository(owner:str, repo:str):
    try:
        return get_repository(owner,repo)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))