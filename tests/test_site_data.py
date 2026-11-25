import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.site_data import build  # noqa: E402

DATA = Path(__file__).resolve().parents[1] / "data" / "sales_data.csv"


@pytest.fixture(scope="module")
def built():
    return build(DATA)


def test_cube_adds_up_to_the_csv(built):
    data, df = built
    assert sum(r[4] for r in data["cube"]) == pytest.approx(df["total_amount"].sum(), rel=1e-9)
    assert sum(r[5] for r in data["cube"]) == len(df) == data["meta"]["orders"]


def test_monthly_actuals_match_cube(built):
    data, df = built
    per = [0.0] * len(data["months"])
    for m, _, _, _, rev, _ in data["cube"]:
        per[m] += rev
    for a, b in zip(per, data["forecast"]["actual"]):
        assert abs(a - b) <= 1


def test_rfm_covers_every_customer_and_all_revenue(built):
    data, df = built
    assert sum(r[1] for r in data["rfm"]) == df["customer_id"].nunique()
    assert sum(r[2] for r in data["rfm"]) == pytest.approx(df["total_amount"].sum(), abs=len(data["rfm"]))


def test_cohort_unobservable_months_are_null_not_zero(built):
    data, _ = built
    last_row = data["cohort"]["values"][-1]
    assert last_row[0] == 100.0 and all(v is None for v in last_row[1:])


def test_future_months_follow_the_data(built):
    data, _ = built
    assert data["months"][-1] == "2025-12" and data["forecast"]["future_months"] == ["2026-01", "2026-02", "2026-03"]
