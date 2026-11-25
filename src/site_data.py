"""Export everything the live explorer shows to docs/data.json, computed from the CSV.

    python src/site_data.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.customer_analysis import SEGMENT_ORDER, cohort_retention, load, pareto, rfm_table  # noqa: E402
from src.forecast import backtest, predict, rolling_backtest  # noqa: E402


def build(path="data/sales_data.csv"):
    df = load(path)
    df["month"] = df["order_date"].dt.to_period("M").astype(str)
    months = sorted(df["month"].unique())
    dims = {"region": sorted(df["region"].unique()), "category": sorted(df["category"].unique()),
            "payment": sorted(df["payment_method"].unique())}
    # cube: one row per month x region x category x payment: [m, r, c, p, revenue, orders]
    g = df.groupby(["month", "region", "category", "payment_method"]).agg(rev=("total_amount", "sum"), n=("order_id", "count")).reset_index()
    cube = [[months.index(r.month), dims["region"].index(r.region), dims["category"].index(r.category),
             dims["payment"].index(r.payment_method), round(r.rev, 2), int(r.n)] for r in g.itertuples()]

    monthly = df.groupby("month")["total_amount"].sum().reindex(months)
    bt = backtest(monthly.values, holdout=6)
    rb = rolling_backtest(monthly.values)
    best = rb[0]["model"]
    fut = predict(best, monthly.values, 3)
    last = pd.Period(months[-1])
    future_months = [str(last + i) for i in (1, 2, 3)]

    rfm = rfm_table(df)
    seg = rfm.groupby("segment", observed=True).agg(customers=("customer_id", "count"), revenue=("monetary", "sum"),
                                                    recency=("recency_days", "median"), freq=("frequency", "mean")).reindex(SEGMENT_ORDER).dropna()
    ret = cohort_retention(df)
    ret = ret.iloc[:, :13]
    share, cum = pareto(df)
    pts = [[round(float(share[i]) * 100, 2), round(float(cum[i]) * 100, 2)] for i in np.linspace(0, len(share) - 1, 60).astype(int)]

    yo = df.assign(year=df["order_date"].dt.year).pivot_table(index="category", columns="year", values="total_amount", aggfunc="sum")
    yoy = [[c, round(float(r[2024])), round(float(r[2025])), round(float((r[2025] / r[2024] - 1) * 100), 1)] for c, r in yo.iterrows()]

    data = {
        "meta": {"orders": int(len(df)), "customers": int(df["customer_id"].nunique()), "revenue": round(float(df["total_amount"].sum()), 2),
                 "first": str(df["order_date"].min().date()), "last": str(df["order_date"].max().date())},
        "months": months, "dims": dims, "cube": cube,
        "forecast": {"holdout": 6, "backtest": bt, "rolling": rb, "best": best, "actual": [round(float(v)) for v in monthly.values],
                     "future_months": future_months, "future": [round(float(v)) for v in fut]},
        "rfm": [[s, int(r.customers), round(float(r.revenue)), float(r.recency), round(float(r.freq), 2)] for s, r in seg.iterrows()],
        "cohort": {"cohorts": [str(c) for c in ret.index],
                   "values": [[None if pd.isna(v) else round(float(v) * 100, 1) for v in row] for row in ret.values],
                   "sizes": [int(x) for x in cohort_sizes(df, ret.index)]},
        "pareto": pts, "pareto_top20": round(float(np.interp(0.2, share, cum)) * 100, 1),
        "yoy": yoy,
    }
    return data, df


def cohort_sizes(df, cohorts):
    first = df.groupby("customer_id")["order_date"].min().dt.to_period("M")
    return [int((first == c).sum()) for c in cohorts]


def filter_fixtures(data, df):
    """A few filter combinations with their expected totals, for the JS parity test."""
    cases = []
    R, C, P = data["dims"]["region"], data["dims"]["category"], data["dims"]["payment"]
    for yr, region, cat in [(None, None, None), (2024, None, None), (2025, "Cairo", None), (None, "Giza", "Books"), (2025, None, "Electronics"), (2024, "Aswan", "Sports")]:
        m = pd.Series(True, index=df.index)
        if yr: m &= df["order_date"].dt.year == yr
        if region: m &= df["region"] == region
        if cat: m &= df["category"] == cat
        cases.append({"year": yr, "region": region, "category": cat, "revenue": round(float(df.loc[m, "total_amount"].sum()), 2), "orders": int(m.sum())})
    return cases


if __name__ == "__main__":
    data, df = build()
    Path("docs").mkdir(exist_ok=True)
    Path("docs/data.json").write_text(json.dumps(data, separators=(",", ":")))
    Path("tests/fixtures").mkdir(parents=True, exist_ok=True)
    Path("tests/fixtures/filters.json").write_text(json.dumps(filter_fixtures(data, df)))
    f = data["forecast"]
    print("holdout:", [(r["model"], r["mape"]) for r in f["backtest"]], "rolling:", [(r["model"], r["mape"], r["origins"]) for r in f["rolling"]], "best:", f["best"], "future:", f["future"])
    print("top20:", data["pareto_top20"], "cube rows:", len(data["cube"]), "size KB:", round(len(json.dumps(data)) / 1024))
