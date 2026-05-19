# upwork-job-triage

I got tired of burning connects on garbage Upwork jobs, so I wrote a scorer.

Point it at a JSON dump of job listings. It hard-rejects the obvious nope
(no verified payment, broke client, post is a week old, 40 proposals already,
wrong stack, CMS spam) and scores whatever is left 0-100 on a weighted rubric.
No LLM, no API calls. Same input gives the same ranking every time, in
milliseconds. The whole thing is a weighted sum. You do not need a model for
arithmetic - keep the model for writing the actual proposal.

I built this for my own filtering as a zero-review senior profile, where you
only get a shot on a narrow slice of jobs, so the gates are tuned to be picky.
Edit `config/rubric.yaml` to make them yours.

## Install

```bash
pip install -e ".[dev]"
```

## Use

```bash
triage jobs.json --rubric config/rubric.yaml --min-score 60
```

```
score  prop      budget  title
------------------------------------------------------------------------
   84     3        $70  Build a Claude API integration for our Python ...
   71     8       $2500  RAG pipeline over internal docs (FastAPI)
```

`--json` dumps the full scored objects: per-criterion subscores, plus the
rejection reason for anything that got filtered.

## Input

A JSON array of jobs. One looks like this:

```json
{
  "id": "~01abc",
  "title": "Claude API integration for Laravel app",
  "description": "We have a Laravel 11 app and want an AI assistant...",
  "skills": ["PHP", "Laravel", "Anthropic"],
  "budget_type": "hourly",
  "budget_min": 40,
  "budget_max": 70,
  "proposals": 4,
  "posted_ago_minutes": 35,
  "client_payment_verified": true,
  "client_total_spend": 18000,
  "client_hire_rate": 0.74,
  "client_country": "United States",
  "url": "https://www.upwork.com/jobs/~01abc"
}
```

Missing fields fall back to sane defaults (see `src/triage/models.py`).

## Rubric

`config/rubric.yaml` owns every threshold and weight. Defaults reject a job if:
payment is not verified, client spend is under $1000, hire rate is below 50%,
more than 15 proposals, posted over 6 hours ago, hourly under $25 or fixed
under $300, it hits a blocklist term (wordpress, shopify, wix, ...), or it has
zero overlap with the skill list.

Survivors get scored: skill match 35, client quality 25, low competition 20,
recency 10, budget fit 10. All of that is in the yaml, none of it is in code.

## Dev

```bash
make test       # pytest
make lint       # ruff
make typecheck  # mypy src
```

MIT, see LICENSE.
