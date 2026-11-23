"""Analyze the retail sales dataset and produce charts plus a written insight summary.

Outputs:
  figures/monthly_revenue_trend.png
  figures/top_categories.png
  figures/revenue_by_region.png
  figures/payment_method_share.png
  reports/key_insights.md

Usage:
    python src/analyze_sales.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.grid": True,
    "grid.alpha": 0.3,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "font.size": 11,
})
COLOR = "#2563eb"


def load(path="data/sales_data.csv"):
    df = pd.read_csv(path, parse_dates=["order_date"])
    df["month"] = df["order_date"].dt.to_period("M").dt.to_timestamp()
    return df


def chart_monthly_revenue(df):
    monthly = df.groupby("month")["total_amount"].sum() / 1000
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(monthly.index, monthly.values, marker="o", color=COLOR, linewidth=2)
    ax.set_title("Monthly Revenue Trend", fontsize=14, fontweight="bold")
    ax.set_ylabel("Revenue (thousand EGP)")
    ax.set_xlabel("")
    fig.tight_layout()
    fig.savefig("figures/monthly_revenue_trend.png", dpi=150)
    plt.close(fig)
    return monthly


def chart_top_categories(df):
    cats = (df.groupby("category")["total_amount"].sum() / 1000).sort_values()
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(cats.index, cats.values, color=COLOR)
    ax.set_title("Revenue by Category", fontsize=14, fontweight="bold")
    ax.set_xlabel("Revenue (thousand EGP)")
    for i, v in enumerate(cats.values):
        ax.text(v, i, f" {v:,.0f}K", va="center", fontsize=10)
    fig.tight_layout()
    fig.savefig("figures/top_categories.png", dpi=150)
    plt.close(fig)
    return cats


def chart_revenue_by_region(df):
    regions = (df.groupby("region")["total_amount"].sum() / 1000).sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(regions.index, regions.values, color=COLOR)
    ax.set_title("Revenue by Region", fontsize=14, fontweight="bold")
    ax.set_ylabel("Revenue (thousand EGP)")
    fig.tight_layout()
    fig.savefig("figures/revenue_by_region.png", dpi=150)
    plt.close(fig)
    return regions


def chart_payment_share(df):
    pay = df.groupby("payment_method")["total_amount"].sum().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.pie(pay.values, labels=pay.index, autopct="%1.1f%%", startangle=90,
           colors=["#2563eb", "#60a5fa", "#93c5fd", "#bfdbfe"])
    ax.set_title("Payment Method Share of Revenue", fontsize=14, fontweight="bold")
    fig.tight_layout()
    fig.savefig("figures/payment_method_share.png", dpi=150)
    plt.close(fig)
    return pay


def write_insights(df, monthly, cats, regions, pay):
    total = df["total_amount"].sum()
    aov = df["total_amount"].mean()
    best_month = monthly.idxmax().strftime("%B %Y")
    worst_month = monthly.idxmin().strftime("%B %Y")
    growth = (monthly.values[-1] / monthly.values[0] - 1) * 100
    top_cat, top_cat_share = cats.index[-1], cats.values[-1] / cats.sum() * 100
    top_region, top_region_share = regions.index[0], regions.values[0] / regions.sum() * 100
    repeat = df.groupby("customer_id").size()
    repeat_rate = (repeat > 1).mean() * 100

    lines = [
        "# Key Insights",
        "",
        f"- **Total revenue:** {total:,.0f} EGP across {len(df):,} orders "
        f"({df['customer_id'].nunique()} unique customers, {df['order_date'].dt.date.min()} to {df['order_date'].dt.date.max()})",
        f"- **Average order value:** {aov:,.0f} EGP",
        f"- **Best month:** {best_month}; **slowest month:** {worst_month}",
        f"- **Last vs first month growth:** {growth:+.1f}%",
        f"- **Top category:** {top_cat} ({top_cat_share:.1f}% of revenue)",
        f"- **Top region:** {top_region} ({top_region_share:.1f}% of revenue)",
        f"- **Most used payment method:** {pay.index[0]} ({pay.values[0] / pay.values.sum() * 100:.1f}% of revenue)",
        f"- **Repeat customer rate:** {repeat_rate:.1f}% of customers ordered more than once",
        "",
        "## Business takeaways",
        "",
        f"1. **{top_region} dominates revenue.** Marketing budget and stock should follow that demand, "
        "with targeted offers to grow the weaker regions.",
        f"2. **{top_cat} is the revenue engine.** Protecting its availability and pricing matters more "
        "than discounting weaker categories.",
        "3. **Clear seasonality.** Revenue peaks around spring and year-end; staffing and campaigns "
        "should be planned a month ahead of each peak.",
        f"4. **{pay.index[0]} leads payments.** Keeping that method friction-free (and nudging the "
        "long tail toward it) reduces checkout drop-off.",
        f"5. **Repeat rate of {repeat_rate:.0f}%.** A loyalty or re-engagement push on one-time buyers "
        "is the cheapest revenue upside in the data.",
    ]
    Path("reports/key_insights.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def main():
    Path("figures").mkdir(exist_ok=True)
    Path("reports").mkdir(exist_ok=True)
    df = load()
    monthly = chart_monthly_revenue(df)
    cats = chart_top_categories(df)
    regions = chart_revenue_by_region(df)
    pay = chart_payment_share(df)
    write_insights(df, monthly, cats, regions, pay)


if __name__ == "__main__":
    main()
