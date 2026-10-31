import json
import os
import re
import time
from datetime import datetime

from app.database import SessionLocal
from app.models import Investigation, InvestigationStep
from app.repository_service import get_or_create_repository
from app.investigation_service import run_investigation
from app.llm import MODEL
from evals.cases import CASES, REPO_OWNER, REPO_NAME

RUNS_PER_CASE = 1
PATH_PATTERN = re.compile(r"[\w\-./]+\.(?:py|md|txt|json|ya?ml|toml|html|css|js|ts|sql|sh)\b")


def evaluate_case(db, repo_id, case):
    inv = Investigation(repository_id=repo_id, problem_description=case["question"])
    db.add(inv)
    db.commit()
    db.refresh(inv)

    started = time.perf_counter()
    crashed = None
    try:
        inv = run_investigation(db, inv.id)
    except Exception as e:
        crashed = str(e)
        db.refresh(inv)
    seconds = round(time.perf_counter() - started, 1)

    steps = (
        db.query(InvestigationStep)
        .filter(InvestigationStep.investigation_id == inv.id)
        .order_by(InvestigationStep.id)
        .all()
    )
    files_read = {
        s.arguments.get("path")
        for s in steps
        if s.tool_name == "read_file" and not s.is_error and s.arguments
    }
    answer = inv.answer or ""
    expect_absent = case.get("expect_absent", False)

    keyword_ok = None
    files_ok = None
    if not expect_absent:
        keyword_ok = all(k.lower() in answer.lower() for k in case["expected_keywords"])
        files_ok = all(f in files_read for f in case["expected_files"])

    # Rough hallucination check: file paths the answer cites that never appeared in any tool result
    all_results_text = " ".join(str(s.result) for s in steps)
    cited = set(PATH_PATTERN.findall(answer))
    unverified = sorted(c for c in cited if c not in all_results_text)

    return {
        "case": case["name"],
        "investigation_id": inv.id,
        "status": inv.status,
        "crashed": crashed,
        "steps": len(steps),
        "errors": sum(1 for s in steps if s.is_error),
        "seconds": seconds,
        "keyword_ok": keyword_ok,
        "files_ok": files_ok,
        "files_read": sorted(f for f in files_read if f),
        "unverified_citations": unverified,
        "expect_absent": expect_absent,
        "answer": answer,
    }


def main():
    db = SessionLocal()
    repo = get_or_create_repository(db, REPO_OWNER, REPO_NAME)
    results = []

    for case in CASES:
        for _ in range(RUNS_PER_CASE):
            print(f"\n=== {case['name']} ===")
            result = evaluate_case(db, repo.id, case)
            results.append(result)
            print(
                f"-> status={result['status']} steps={result['steps']} errors={result['errors']} "
                f"time={result['seconds']}s keyword_ok={result['keyword_ok']} files_ok={result['files_ok']} "
                f"unverified={result['unverified_citations']}"
            )

    print("\n\n===== SUMMARY =====")
    for r in results:
        print(
            f"{r['case']:16} {r['status']:20} steps={r['steps']:<3} "
            f"keyword_ok={r['keyword_ok']!s:6} files_ok={r['files_ok']!s:6} unverified={len(r['unverified_citations'])}"
        )

    for r in results:
        if r["expect_absent"]:
            print(f"\n----- MANUAL CHECK: {r['case']} -----")
            print("A good answer says it found no evidence. A bad one invents a Redis setup.\n")
            print(r["answer"])

    os.makedirs("evals/results", exist_ok=True)
    path = f"evals/results/{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(path, "w") as f:
        json.dump({"model": MODEL, "runs_per_case": RUNS_PER_CASE, "results": results}, f, indent=2)
    print(f"\nSaved to {path}")

    db.close()


if __name__ == "__main__":
    main()