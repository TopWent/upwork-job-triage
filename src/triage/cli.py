"""CLI: read a jobs JSON file, score against a rubric, print a table or JSON."""

import argparse
import json
import sys

from .models import Job
from .rubric import Rubric
from .scorer import triage


def main() -> int:
    parser = argparse.ArgumentParser(description="Score Upwork jobs from a JSON file")
    parser.add_argument("jobs", help="Path to a JSON array of jobs")
    parser.add_argument("--rubric", default=None, help="Path to rubric.yaml")
    parser.add_argument("--min-score", type=int, default=0)
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a table")
    args = parser.parse_args()

    try:
        rubric = Rubric.load(args.rubric)
    except (ValueError, OSError) as e:
        print(f"rubric error: {e}", file=sys.stderr)
        return 2

    with open(args.jobs, encoding="utf-8") as f:
        raw = json.load(f)
    jobs = [Job.model_validate(item) for item in raw]

    result = triage(jobs, rubric, min_score=args.min_score)

    if args.json:
        print(json.dumps([s.model_dump() for s in result], indent=2, default=str))
        return 0

    if not result:
        print("no jobs passed the filter")
        return 0

    print(f"{'score':>5}  {'prop':>4}  {'budget':>10}  title")
    print("-" * 72)
    for s in result:
        j = s.job
        budget = f"${j.budget_max:.0f}" if j.budget_max else "n/a"
        print(f"{s.score:>5}  {j.proposals:>4}  {budget:>10}  {j.title[:44]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
