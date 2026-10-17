#This is the db logic that calls the investigate function and saves all the function calls to the investigationSteps table
from sqlalchemy.orm import Session
from app.models import Investigation, InvestigationStep, Repository
from app.agent import investigate


def run_investigation(db: Session, investigation_id: int) -> Investigation:
    investigation = db.query(Investigation).filter(Investigation.id == investigation_id).first()
    if not investigation:
        raise ValueError(f"Investigation {investigation_id} not found")

    repository = db.query(Repository).filter(Repository.id == investigation.repository_id).first()
    owner, repo = repository.full_name.split("/")

    investigation.status = "running"
    db.commit()
#This function is a callback, i.e. the run_investigation tells the investigate function "call this when something(defined in investigat function) happens", so that investigate calls save_step after each tool finishes.
#Closure. A function defined inside another function can use the outer function’s variables, and it keeps hold of them even after it’s handed somewhere else.
    def save_step(step_number, tool_name, args, result):
        db.add(InvestigationStep(
            investigation_id=investigation.id,
            step_number=step_number,
            tool_name=tool_name,
            arguments=args,
            result=result,
            is_error="error" in result,
        ))
        db.commit()

    try:
        outcome = investigate(owner, repo, investigation.problem_description, on_step=save_step)
        investigation.status = outcome["status"]
        investigation.answer = outcome["answer"]
    except Exception:
        #rollback throws away all the changes that are staged but not commited yet when a crash happens to keep the session clean. It wont let you change the status or call db.commit() or anything at all until you rollback. Steps that were already committed stay in the table.
        db.rollback()
        investigation.status = "failed"
        db.commit()
        raise

    db.commit()
    db.refresh(investigation)
    return investigation