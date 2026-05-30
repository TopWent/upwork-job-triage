"""Deterministic Upwork job filter and scorer.

Hard-reject gates first, then a weighted 0-100 score on whatever survives.
No LLM, no network. Same job + same rubric always gives the same number.
"""

from __future__ import annotations

import re

from .models import BudgetType, Job, ScoredJob, Verdict
from .rubric import Rubric

# A "chunk" is a run of letters/digits plus the few tech punctuation chars we
# care about keeping (c++, c#, .net). We then split each chunk on dots and
# hyphens so a domain like wordpress.com also yields the bare word "wordpress".
_CHUNK = re.compile(r"[a-z0-9+#.-]+")


def _tokens(text: str) -> set[str]:
    out: set[str] = set()
    for chunk in _CHUNK.findall(text.lower()):
        out.add(chunk)
        # Also index the dotted/hyphenated parts so "wordpress" falls out of
        # "wordpress.com" and trailing punctuation ("wordpress.") drops off.
        # node.js / sentence-transformers still survive as the whole chunk.
        for part in re.split(r"[.-]", chunk):
            if part:
                out.add(part)
    return out


def hard_reject(job: Job, r: Rubric) -> str | None:
    if r.require_payment_verified and not job.client_payment_verified:
        return "payment not verified"
    if job.client_total_spend < r.min_spend:
        return f"client spend ${job.client_total_spend:.0f} < ${r.min_spend:.0f}"
    if job.client_hire_rate < r.min_hire_rate:
        return f"hire rate {job.client_hire_rate:.0%} < {r.min_hire_rate:.0%}"
    if job.proposals > r.max_proposals:
        return f"{job.proposals} proposals > {r.max_proposals}"
    if job.posted_ago_minutes > r.max_age_minutes:
        return f"posted {job.posted_ago_minutes} min ago > {r.max_age_minutes}"
    if job.budget_type == BudgetType.HOURLY and job.budget_max and job.budget_max < r.min_hourly:
        return f"hourly ${job.budget_max:.0f} < ${r.min_hourly:.0f}"
    if job.budget_type == BudgetType.FIXED and job.budget_max and job.budget_max < r.min_fixed:
        return f"fixed ${job.budget_max:.0f} < ${r.min_fixed:.0f}"
    blocked = _blocklisted(job, r)
    if blocked is not None:
        return f"blocked term: {blocked}"
    if not _skill_overlap(job, r):
        return "no stack overlap"
    return None


def _blocklisted(job: Job, r: Rubric) -> str | None:
    tokens = _tokens(job.title) | _tokens(job.description)
    for s in job.skills:
        tokens |= _tokens(s)
    raw = " ".join([job.title, job.description, *job.skills]).lower()
    for term in r.blocklist:
        term = term.lower()
        # Multi-word terms ("go high level") can't live in the token set, so
        # match those as a phrase against the raw text. Single words match
        # token-wise to avoid "react" firing inside "reactor".
        if " " in term:
            if term in raw:
                return term
        elif term in tokens:
            return term
    return None


def _skill_overlap(job: Job, r: Rubric) -> set[str]:
    haystack = _tokens(job.title) | _tokens(job.description)
    for s in job.skills:
        haystack |= _tokens(s)
    return haystack & {s.lower() for s in r.skills}


def _skill_score(job: Job, r: Rubric) -> int:
    hits = len(_skill_overlap(job, r))
    if hits == 0:
        return 0
    return min(r.w_skill, round(r.w_skill * min(hits, 6) / 6))


def _client_score(job: Job, r: Rubric) -> int:
    spend_pts = min(1.0, job.client_total_spend / 50_000) * (r.w_client * 0.6)
    hire_pts = min(1.0, job.client_hire_rate) * (r.w_client * 0.4)
    return round(spend_pts + hire_pts)


def _competition_score(job: Job, r: Rubric) -> int:
    if job.proposals <= 0:
        return r.w_competition
    ratio = max(0.0, 1.0 - job.proposals / (r.max_proposals + 1))
    return round(r.w_competition * ratio)


def _recency_score(job: Job, r: Rubric) -> int:
    if job.posted_ago_minutes <= 0:
        return r.w_recency
    ratio = max(0.0, 1.0 - job.posted_ago_minutes / (r.max_age_minutes + 1))
    return round(r.w_recency * ratio)


def _budget_score(job: Job, r: Rubric) -> int:
    if job.budget_type == BudgetType.HOURLY:
        rate = job.budget_max or job.budget_min
        if rate <= 0:
            return round(r.w_budget * 0.5)
        return round(r.w_budget * min(1.0, rate / r.target_hourly))
    value = job.budget_max or job.budget_min
    if value <= 0:
        return round(r.w_budget * 0.5)
    return round(r.w_budget * min(1.0, value / (r.target_hourly * 40)))


def score_job(job: Job, r: Rubric) -> ScoredJob:
    """Reject on the hard gates, else return a 0-100 score with subscores."""
    rejection = hard_reject(job, r)
    if rejection is not None:
        return ScoredJob(job=job, verdict=Verdict.REJECT, score=0, reason=rejection)

    subs = {
        "skill": _skill_score(job, r),
        "client": _client_score(job, r),
        "competition": _competition_score(job, r),
        "recency": _recency_score(job, r),
        "budget": _budget_score(job, r),
    }
    total = sum(subs.values())
    top = sorted(subs.items(), key=lambda kv: kv[1], reverse=True)[:2]
    reason = "strong on " + ", ".join(k for k, _ in top)
    return ScoredJob(job=job, verdict=Verdict.TAKE, score=total, reason=reason, subscores=subs)


def triage(jobs: list[Job], r: Rubric, min_score: int = 0) -> list[ScoredJob]:
    """Score every job, keep the takes at or above min_score, best first."""
    scored = [score_job(j, r) for j in jobs]
    taken = [s for s in scored if s.verdict == Verdict.TAKE and s.score >= min_score]
    taken.sort(key=lambda s: s.score, reverse=True)
    return taken
