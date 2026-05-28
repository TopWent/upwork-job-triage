import pytest
from pydantic import ValidationError

from triage.models import BudgetType, Job


def make(**over):
    base = dict(id="1", title="x", budget_type=BudgetType.HOURLY)
    base.update(over)
    return Job(**base)


def test_hire_rate_must_be_a_fraction():
    with pytest.raises(ValidationError):
        make(client_hire_rate=2.5)


def test_negative_spend_rejected():
    with pytest.raises(ValidationError):
        make(client_total_spend=-1)


def test_negative_proposals_rejected():
    with pytest.raises(ValidationError):
        make(proposals=-3)


def test_sane_values_ok():
    j = make(client_hire_rate=1.0, client_total_spend=0, budget_max=70)
    assert j.client_hire_rate == 1.0
