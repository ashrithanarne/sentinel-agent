from fastapi import FastAPI, HTTPException
from app.github_service import get_repository, read_file, search_repository, list_directory

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

@app.get("/repo/{owner}/{repo}/file")
def get_file(owner:str, repo:str, path:str):
    try:
        return read_file(owner,repo,path)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/repo/{owner}/{repo}/search")
def search_repo(owner: str, repo: str, q: str):
    try:
        return search_repository(owner, repo, q)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e)) 

@app.get("/repo/{owner}/{repo}/dir")
def get_directory(owner: str, repo: str, path: str = ""):
    try:
        return list_directory(owner, repo, path)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))