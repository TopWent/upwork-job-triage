from enum import StrEnum

from pydantic import BaseModel, Field


class BudgetType(StrEnum):
    HOURLY = "hourly"
    FIXED = "fixed"


class Job(BaseModel):
    id: str = Field(min_length=1)
    title: str
    description: str = ""
    skills: list[str] = Field(default_factory=list)

    budget_type: BudgetType
    budget_min: float = 0.0
    budget_max: float = 0.0

    proposals: int = 0
    posted_ago_minutes: int = 0

    client_payment_verified: bool = False
    client_total_spend: float = 0.0
    client_hire_rate: float = 0.0
    client_country: str = ""

    url: str = ""


class Verdict(StrEnum):
    TAKE = "take"
    REJECT = "reject"


class ScoredJob(BaseModel):
    job: Job
    verdict: Verdict
    score: int
    reason: str
    subscores: dict[str, int] = Field(default_factory=dict)
