import glob
import json

from app.database import SessionLocal
from app.models import InvestigationStep
from evals.quote_check import check_quotes

latest = sorted(glob.glob("evals/results/*.json"))[-1]
data = json.load(open(latest))
db = SessionLocal()
print(latest)
for r in data["results"]:
    steps = (
        db.query(InvestigationStep)
        .filter(InvestigationStep.investigation_id == r["investigation_id"])
        .order_by(InvestigationStep.id)
        .all()
    )
    total, missing = check_quotes(r["answer"], steps)
    print(f"{r['case']:16} snippets={total} unmatched={len(missing)}")
    for m in missing:
        print("    UNMATCHED:", m[:120])
db.close()