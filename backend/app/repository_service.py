#It is like a helper function for the endpoints
from sqlalchemy.orm import Session
from app.models import Repository
from app.github_service import get_repository

# This is a function that other endpoint functions can call, its not an endpoint itsef. THese are service functions.
# It is used to rduce redundant codes in the endpoint 
def get_or_create_repository(db: Session, owner: str, repo: str) -> Repository:
    full_name = f"{owner}/{repo}"
    existing = db.query(Repository).filter(Repository.full_name == full_name).first()
    if existing:
        return existing

    data = get_repository(owner, repo)  # raises if GitHub lookup fails

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
    return new_repo