import glob
import json

latest = sorted(glob.glob("evals/results/*.json"))[-1]
data = json.load(open(latest))
print(latest)
for r in data["results"]:
    print(f"{r['case']:16} {r['status']:20} {r['steps']} steps  {r['seconds']}s")
    if r.get("crashed"):
        print("    crashed:", r["crashed"][:400])