import math

import pytest

from app.insert_data.utils import parse_score


@pytest.mark.parametrize("score,expected", [
    ("2–1", (2, 1, None, None)),
    ("10–0", (10, 0, None, None)),          # was parsed as 0-1
    ("0–12", (0, 12, None, None)),
    ("(4) 1–1 (3)", (1, 1, 4, 3)),          # penalty shoot-out
    ("(10) 2–2 (11)", (2, 2, 10, 11)),
    (None, (None, None, None, None)),
    (math.nan, (None, None, None, None)),
    ("postponed", (None, None, None, None)),
])
def test_parse_score(score, expected):
    assert parse_score(score) == expected
