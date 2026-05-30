from triage.models import BudgetType, Job, Verdict
from triage.rubric import Rubric
from triage.scorer import hard_reject, score_job, triage

R = Rubric()


def good_job(**over) -> Job:
    base = dict(
        id="1",
        title="Build a Claude API integration for our Python backend",
        description="We need an LLM integration with FastAPI and PostgreSQL.",
        skills=["Python", "FastAPI", "Anthropic"],
        budget_type=BudgetType.HOURLY,
        budget_min=40,
        budget_max=70,
        proposals=3,
        posted_ago_minutes=30,
        client_payment_verified=True,
        client_total_spend=25_000,
        client_hire_rate=0.8,
    )
    base.update(over)
    return Job(**base)


def test_clean_job_is_taken():
    s = score_job(good_job(), R)
    assert s.verdict is Verdict.TAKE
    assert s.score > 50
    assert set(s.subscores) == {"skill", "client", "competition", "recency", "budget"}


def test_reject_unverified_payment():
    assert hard_reject(good_job(client_payment_verified=False), R) == "payment not verified"


def test_reject_low_spend():
    msg = hard_reject(good_job(client_total_spend=200), R)
    assert "spend" in msg


def test_reject_low_hire_rate():
    msg = hard_reject(good_job(client_hire_rate=0.2), R)
    assert "hire rate" in msg


def test_reject_too_many_proposals():
    msg = hard_reject(good_job(proposals=40), R)
    assert "proposals" in msg


def test_reject_stale_job():
    msg = hard_reject(good_job(posted_ago_minutes=1000), R)
    assert "posted" in msg


def test_reject_low_hourly():
    msg = hard_reject(good_job(budget_type=BudgetType.HOURLY, budget_max=10), R)
    assert "hourly" in msg


def test_reject_low_fixed():
    msg = hard_reject(good_job(budget_type=BudgetType.FIXED, budget_min=100, budget_max=100), R)
    assert "fixed" in msg


def test_reject_stack_mismatch():
    msg = hard_reject(
        good_job(
            title="Photoshop banner designer needed",
            description="Pure visual design work, Photoshop only",
            skills=["Photoshop", "Graphic Design"],
        ),
        R,
    )
    assert msg == "no stack overlap"


def test_reject_cms_job():
    msg = hard_reject(
        good_job(
            title="WordPress theme designer needed",
            description="Photoshop and CSS only",
            skills=["WordPress", "CSS"],
        ),
        R,
    )
    assert msg == "blocked term: wordpress"


def test_reject_cms_even_with_matching_skill_keyword():
    # "api" is in the skills list, so skill-overlap alone would pass.
    # The blocklist must still reject it because it is a CMS job.
    msg = hard_reject(
        good_job(
            title="Shopify store with a custom REST API",
            description="Need a Shopify expert, some API work",
            skills=["Shopify", "API"],
        ),
        R,
    )
    assert msg == "blocked term: shopify"


def test_reject_cms_when_glued_to_a_domain():
    # The word is only present as part of a domain. Old tokenizer kept
    # "wordpress.com" as one token and the blocklist never fired.
    msg = hard_reject(
        good_job(
            title="Migrate our site",
            description="Everything lives on wordpress.com and we want it moved.",
            skills=["Python"],
        ),
        R,
    )
    assert msg == "blocked term: wordpress"


def test_multiword_blocklist_phrase_matches():
    r = Rubric(blocklist=["go high level"])
    # "go" alone is a real skill, so this must match the whole phrase, not "go".
    msg = hard_reject(
        good_job(
            title="Need a Go High Level funnel built",
            description="GHL automation, no real backend.",
            skills=["Python"],
        ),
        r,
    )
    assert msg == "blocked term: go high level"


def test_dotted_skill_token_still_matches():
    # node.js must still register as an overlapping skill, not get swallowed.
    r = Rubric(skills=["node.js"], blocklist=[])
    s = score_job(
        good_job(
            title="Build a Node.js service",
            description="Plain node.js backend work.",
            skills=["Node.js"],
        ),
        r,
    )
    assert s.verdict is Verdict.TAKE


def test_score_monotonic_in_competition():
    few = score_job(good_job(proposals=1), R).score
    many = score_job(good_job(proposals=14), R).score
    assert few > many


def test_score_monotonic_in_recency():
    fresh = score_job(good_job(posted_ago_minutes=5), R).score
    old = score_job(good_job(posted_ago_minutes=300), R).score
    assert fresh > old


def test_higher_spend_scores_higher():
    low = score_job(good_job(client_total_spend=1500), R).score
    high = score_job(good_job(client_total_spend=80_000), R).score
    assert high > low


def test_triage_sorts_and_filters():
    jobs = [
        good_job(id="a", proposals=1),
        good_job(id="b", proposals=14),
        good_job(id="c", client_payment_verified=False),
    ]
    result = triage(jobs, R, min_score=0)
    ids = [s.job.id for s in result]
    assert ids == ["a", "b"]
    assert all(s.score >= 0 for s in result)
    assert result[0].score >= result[1].score


def test_triage_respects_min_score():
    jobs = [good_job(id="a"), good_job(id="b", title="generic api work", skills=["api"])]
    high_only = triage(jobs, R, min_score=90)
    assert all(s.score >= 90 for s in high_only)


def test_skill_score_caps_at_weight():
    s = score_job(good_job(), R)
    assert s.subscores["skill"] <= R.w_skill
    assert s.subscores["client"] <= R.w_client
    assert s.subscores["competition"] <= R.w_competition
