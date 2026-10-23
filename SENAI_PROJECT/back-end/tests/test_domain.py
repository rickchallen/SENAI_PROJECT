from datetime import datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.domain import (
    calculate_base_value,
    calculate_overall,
    market_value,
    remaining_days,
)


@pytest.mark.parametrize(
    ("condition", "agility", "age", "expected"),
    [
        ("APTO", 20, 25, "82.00"),
        ("APTO", 50, 19, "90.20"),
        ("MAL_CONDICIONADO", 80, 21, "84.05"),
        ("DOENTE", 10, 40, "49.20"),
    ],
)
def test_market_value_uses_condition_agility_age_and_rounding(
    condition, agility, age, expected
):
    player = SimpleNamespace(
        valor_base=Decimal("82.00"),
        condicao=condition,
        agilidade=agility,
        idade=age,
    )
    assert market_value(player) == Decimal(expected)


def test_overall_and_base_value_round_half_up():
    assert calculate_overall("ZAG", (50, 90, 60, 40, 80, 75)) == 73
    assert calculate_base_value(70, 84, 21) == Decimal("34.20")


def test_remaining_days_rounds_any_fraction_up():
    moment = datetime(2026, 11, 5, 16, 40)
    remaining = moment + timedelta(days=116, hours=17, minutes=35)
    assert remaining_days(remaining, moment) == 117
    assert remaining_days(moment, moment) == 0
