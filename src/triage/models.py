"""Input/output schemas. Job is what comes off the Upwork JSON dump."""

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
    budget_min: float = Field(default=0.0, ge=0)
    budget_max: float = Field(default=0.0, ge=0)

    proposals: int = Field(default=0, ge=0)
    posted_ago_minutes: int = Field(default=0, ge=0)

    client_payment_verified: bool = False
    client_total_spend: float = Field(default=0.0, ge=0)
    client_hire_rate: float = Field(default=0.0, ge=0, le=1)
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
