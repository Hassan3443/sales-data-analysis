"""Customer-level analysis: RFM segmentation, cohort retention and Pareto concentration.

Outputs:
  figures/rfm_segments.png            customers and revenue per RFM segment
  figures/cohort_retention.png        monthly cohort retention heatmap
  figures/pareto_customers.png        cumulative revenue vs share of customers
  reports/rfm_segments.csv            one row per customer with R/F/M scores and segment
  reports/customer_insights.md        written findings

Usage:
    python src/customer_analysis.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.rcParams.update({
    "figure.facecolor": "white", "axes.grid": True, "grid.alpha": 0.3,
    "axes.spines.top": False, "axes.spines.right": False, "font.size": 11,
})
COLOR = "#2563eb"

SEGMENT_ORDER = ["Champions", "Loyal", "Potential Loyalist", "New Customers",
                 "At Risk", "Hibernating"]


def load(path="data/sales_data.csv"):
    return pd.read_csv(path, parse_dates=["order_date"])


def quintile_score(series, ascending=True):
    """Score 1-5 using rank-based quintiles (robust to many ties)."""
    ranks = series.rank(method="first", ascending=ascending)
    return pd.qcut(ranks, 5, labels=[1, 2, 3, 4, 5]).astype(int)


def assign_segment(row):
    r, f, m = row["r_score"], row["f_score"], row["m_score"]
    if r >= 4 and f >= 4:
        return "Champions"
    if f >= 4 and r >= 3:
        return "Loyal"
    if r >= 4 and f <= 2:
        return "New Customers"
    if r >= 3 and f >= 2:
        return "Potential Loyalist"
    if r <= 2 and (f >= 3 or m >= 4):
        return "At Risk"
    return "Hibernating"


def rfm_table(df, as_of=None):
    """Recency (days since last order), Frequency (orders) and Monetary (revenue) per customer."""
    as_of = as_of or (df["order_date"].max() + pd.Timedelta(days=1))
    g = df.groupby("customer_id").agg(
        recency_days=("order_date", lambda s: (as_of - s.max()).days),
        frequency=("order_id", "nunique"),
        monetary=("total_amount", "sum"),
    )
    g["r_score"] = quintile_score(g["recency_days"], ascending=False)  # recent = high score
    # Frequency has many ties (most customers order 1-3 times), so use fixed bands
    # instead of quintiles: ties must score the same, not be split arbitrarily.
    g["f_score"] = pd.cut(g["frequency"], [0, 1, 2, 3, 4, np.inf], labels=[1, 2, 3, 4, 5]).astype(int)
    g["m_score"] = quintile_score(g["monetary"])
    g["segment"] = g.apply(assign_segment, axis=1)
    g["segment"] = pd.Categorical(g["segment"], SEGMENT_ORDER, ordered=True)
    return g.reset_index()


def cohort_retention(df):
    """Share of each first-purchase-month cohort that orders again in later months."""
    d = df[["customer_id", "order_date"]].copy()
    d["order_month"] = d["order_date"].dt.to_period("M")
    d["cohort"] = d.groupby("customer_id")["order_month"].transform("min")
    d["age"] = (d["order_month"] - d["cohort"]).apply(lambda x: x.n)
    counts = d.groupby(["cohort", "age"])["customer_id"].nunique().unstack(fill_value=0)
    ret = counts.div(counts[0], axis=0)
    # Months a cohort has not lived through yet are unknown, not zero.
    last = d["order_month"].max()
    for cohort in ret.index:
        observable = (last - cohort).n
        ret.loc[cohort, ret.columns > observable] = np.nan
    return ret


def pareto(df):
    spend = df.groupby("customer_id")["total_amount"].sum().sort_values(ascending=False)
    cum_rev = spend.cumsum() / spend.sum()
    share = np.arange(1, len(spend) + 1) / len(spend)
    return share, cum_rev.values


def chart_rfm(rfm):
    summary = rfm.groupby("segment", observed=True).agg(
        customers=("customer_id", "count"), revenue=("monetary", "sum")).reindex(SEGMENT_ORDER).dropna()
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    axes[0].barh(summary.index[::-1], summary["customers"][::-1], color=COLOR)
    axes[0].set_title("Customers per segment", fontweight="bold")
    axes[1].barh(summary.index[::-1], summary["revenue"][::-1] / 1000, color="#10b981")
    axes[1].set_title("Revenue per segment (thousand EGP)", fontweight="bold")
    fig.suptitle("RFM customer segmentation", fontsize=14, fontweight="bold")
    fig.tight_layout()
    fig.savefig("figures/rfm_segments.png", dpi=150)
    plt.close(fig)
    return summary


def chart_cohort(ret):
    ret = ret.iloc[:, 1:13]
    fig, ax = plt.subplots(figsize=(11, 7))
    ax.set_facecolor("#e5e7eb")
    im = ax.imshow(ret.values * 100, cmap="Blues", aspect="auto", vmin=0, vmax=15)
    ax.set_xticks(range(ret.shape[1]))
    ax.set_xticklabels(ret.columns)
    ax.set_yticks(range(len(ret)))
    ax.set_yticklabels([str(c) for c in ret.index], fontsize=8)
    ax.set_xlabel("Months since first purchase")
    ax.set_title("Cohort retention: % of cohort ordering again (grey = not observable yet)", fontsize=14, fontweight="bold")
    ax.grid(False)
    fig.colorbar(im, ax=ax, label="% of cohort")
    fig.tight_layout()
    fig.savefig("figures/cohort_retention.png", dpi=150)
    plt.close(fig)


def chart_pareto(share, cum_rev):
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(share * 100, cum_rev * 100, color=COLOR, linewidth=2)
    ax.plot([0, 100], [0, 100], "--", color="gray", label="perfect equality")
    ax.set_xlabel("% of customers (biggest spenders first)")
    ax.set_ylabel("% of revenue")
    ax.set_title("Revenue concentration (Pareto curve)", fontsize=14, fontweight="bold")
    ax.legend()
    fig.tight_layout()
    fig.savefig("figures/pareto_customers.png", dpi=150)
    plt.close(fig)


def write_report(rfm, summary, ret, share, cum_rev):
    total = rfm["monetary"].sum()
    top20 = float(np.interp(0.2, share, cum_rev)) * 100
    seg = summary.copy()
    seg["pct_customers"] = seg["customers"] / seg["customers"].sum() * 100
    seg["pct_revenue"] = seg["revenue"] / total * 100
    m1 = ret[1].mean() * 100
    m3 = ret[3].mean() * 100
    lines = [
        "# Customer Insights",
        "",
        f"- **{len(rfm):,} customers**, {total:,.0f} EGP total revenue",
        f"- **Top 20% of customers generate {top20:.0f}% of revenue** (Pareto curve in `figures/pareto_customers.png`)",
        f"- Average cohort retention: **{m1:.1f}%** order again one month after first purchase, **{m3:.1f}%** after three months",
        "",
        "## RFM segments",
        "",
        "| Segment | Customers | % of customers | Revenue (EGP) | % of revenue |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for name, r in seg.iterrows():
        lines.append(f"| {name} | {int(r['customers']):,} | {r['pct_customers']:.1f}% | {r['revenue']:,.0f} | {r['pct_revenue']:.1f}% |")
    lines += [
        "",
        "Scores: Recency (days since last order, lower is better), Frequency (orders), Monetary (revenue), "
        "each scored 1-5 (quintiles for R and M, fixed bands for F: 1, 2, 3, 4, 5+ orders). Segment rules live in `assign_segment` in `src/customer_analysis.py`.",
        "",
        "## What to do with it",
        "",
        "1. **Champions and Loyal:** protect them with early access and loyalty perks; they carry a disproportionate share of revenue.",
        "2. **At Risk:** high past value but gone quiet. A win-back offer here has the best return per message sent.",
        "3. **New Customers:** a second purchase within 30-60 days is what turns them into Loyal customers; trigger a follow-up offer.",
        "4. **Hibernating:** low value and inactive. Cheap, automated re-engagement only.",
    ]
    Path("reports/customer_insights.md").write_text("\n".join(lines) + "\n")


def main():
    Path("figures").mkdir(exist_ok=True)
    Path("reports").mkdir(exist_ok=True)
    df = load()
    rfm = rfm_table(df)
    rfm.to_csv("reports/rfm_segments.csv", index=False)
    summary = chart_rfm(rfm)
    ret = cohort_retention(df)
    chart_cohort(ret)
    share, cum_rev = pareto(df)
    chart_pareto(share, cum_rev)
    write_report(rfm, summary, ret, share, cum_rev)
    print(summary)
    print("Wrote figures/rfm_segments.png, cohort_retention.png, pareto_customers.png and reports/customer_insights.md")


if __name__ == "__main__":
    main()
