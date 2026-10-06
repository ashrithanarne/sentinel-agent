from fastapi import FastAPI, HTTPException, Depends
from app.github_service import get_repository, read_file, search_repository, list_directory
from app import database

from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Repository, Investigation

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
    full_name = f"{owner}/{repo}"
    existing = db.query(Repository).filter(Repository.full_name == full_name).first()

    if existing:
        return {
            "name": existing.name,
            "full_name": existing.full_name,
            "description": existing.description,
            "default_branch": existing.default_branch,
            "private": existing.private,
        }

    try:
        data = get_repository(owner, repo)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

    new_repo = Repository(
        name=data["name"],
        full_name=data["full_name"],
        description=data["description"],
        default_branch=data["default_branch"],
        private=data["private"],
    )
    db.add(new_repo)
    db.commit()

    return data

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
    full_name = f"{request.owner}/{request.repo}"
    repository = db.query(Repository).filter(Repository.full_name == full_name).first()

    if not repository:
        try:
            data = get_repository(request.owner, request.repo)
        except Exception as e:
            raise HTTPException(status_code=404, detail=str(e))

        repository = Repository(
            name=data["name"],
            full_name=data["full_name"],
            description=data["description"],
            default_branch=data["default_branch"],
            private=data["private"],
        )
        db.add(repository)
        db.commit()
        db.refresh(repository)

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