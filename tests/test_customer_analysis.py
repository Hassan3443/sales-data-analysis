import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.customer_analysis import SEGMENT_ORDER, cohort_retention, load, pareto, rfm_table  # noqa: E402


@pytest.fixture(scope="module")
def df():
    return load(Path(__file__).resolve().parents[1] / "data" / "sales_data.csv")


def test_rfm_one_row_per_customer(df):
    rfm = rfm_table(df)
    assert len(rfm) == df["customer_id"].nunique()
    assert rfm["monetary"].sum() == pytest.approx(df["total_amount"].sum())


def test_rfm_scores_in_range_and_segments_known(df):
    rfm = rfm_table(df)
    for col in ["r_score", "f_score", "m_score"]:
        assert rfm[col].between(1, 5).all()
    assert set(rfm["segment"].astype(str)) <= set(SEGMENT_ORDER)


def test_recent_buyers_score_higher_recency():
    data = pd.DataFrame({
        "order_id": range(10),
        "customer_id": [f"C{i}" for i in range(10)],
        "order_date": pd.date_range("2025-01-01", periods=10, freq="30D"),
        "total_amount": [100.0] * 10,
    })
    rfm = rfm_table(data).set_index("customer_id")
    assert rfm.loc["C9", "r_score"] > rfm.loc["C0", "r_score"]


def test_cohort_first_month_is_100_percent(df):
    ret = cohort_retention(df)
    assert (ret[0] == 1).all()
    assert ((ret.fillna(0) >= 0) & (ret.fillna(0) <= 1)).all().all()
    assert ret.loc[ret.index[-1]].isna().sum() == ret.shape[1] - 1


def test_pareto_curve_is_monotonic_and_ends_at_one(df):
    share, cum = pareto(df)
    assert cum[-1] == pytest.approx(1.0)
    assert (cum[1:] >= cum[:-1]).all()
    assert share[-1] == pytest.approx(1.0)
