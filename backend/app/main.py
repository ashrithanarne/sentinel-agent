from fastapi import FastAPI, HTTPException, Depends
from app.github_service import get_repository, read_file, search_repository, list_directory
from app import database

from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Repository, Investigation, InvestigationStep
from app.repository_service import get_or_create_repository
from app.investigation_service import run_investigation, InvestigationNotRunnable

app=FastAPI()

from pydantic import BaseModel

class InvestigationCreate(BaseModel):
    owner: str
    repo: str
    problem_description: str

@app.get("/health")
def health():
    return {"status":"ok"}

@app.get("/repo/{owner}/{repo}")
def read_repository(owner: str, repo: str, db: Session = Depends(get_db)):
    try:
        repository = get_or_create_repository(db, owner, repo)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

    return {
        "name": repository.name,
        "full_name": repository.full_name,
        "description": repository.description,
        "default_branch": repository.default_branch,
        "private": repository.private,
    }

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
    

@app.post("/repo/{owner}/{repo}/save")
def save_repository(owner: str, repo: str, db: Session = Depends(get_db)):
    try:
        data = get_repository(owner, repo)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

    existing = db.query(Repository).filter(Repository.full_name == data["full_name"]).first()
    if existing:
        return {"message": "already saved", "repository": data}

    new_repo = Repository(
        name=data["name"],
        full_name=data["full_name"],
        description=data["description"],
        default_branch=data["default_branch"],
        private=data["private"],
    )
    db.add(new_repo)
    db.commit()
    db.refresh(new_repo)

    return {"message": "saved", "id": new_repo.id}


@app.get("/repos")
def list_repositories(db: Session = Depends(get_db)):
    return db.query(Repository).all()

@app.post("/investigations")
def create_investigation(request: InvestigationCreate, db: Session = Depends(get_db)):
    try:
        repository = get_or_create_repository(db, request.owner, request.repo)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

    investigation = Investigation(
        repository_id=repository.id,
        problem_description=request.problem_description,
    )
    db.add(investigation)
    db.commit()
    db.refresh(investigation)

    return {
        "id": investigation.id,
        "repository": repository.full_name,
        "problem_description": investigation.problem_description,
        "status": investigation.status,
    }

@app.post("/investigations/{investigation_id}/run")
def run_investigation_endpoint(investigation_id: int, db: Session = Depends(get_db)):
    try:
        investigation = run_investigation(db, investigation_id)
    except InvestigationNotRunnable as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Investigation failed: {e}")

    return {
        "id": investigation.id,
        "status": investigation.status,
        "answer": investigation.answer,
    }


@app.get("/investigations/{investigation_id}")
def get_investigation(investigation_id: int, db: Session = Depends(get_db)):
    investigation = db.query(Investigation).filter(Investigation.id == investigation_id).first()
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")

    repository = db.query(Repository).filter(Repository.id == investigation.repository_id).first()
    steps = (
        db.query(InvestigationStep)
        .filter(InvestigationStep.investigation_id == investigation_id)
        .order_by(InvestigationStep.id)
        .all()
    )

    return {
        "id": investigation.id,
        "repository": repository.full_name,
        "problem_description": investigation.problem_description,
        "status": investigation.status,
        "answer": investigation.answer,
        "steps": [
            {
                "step_number": s.step_number,
                "tool": s.tool_name,
                "arguments": s.arguments,
                "is_error": s.is_error,
                "result_preview": str(s.result)[:200],
            }
            for s in steps
        ],
    }