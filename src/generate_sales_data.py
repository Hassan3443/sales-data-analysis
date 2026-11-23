"""Generate a realistic two-year retail sales dataset (synthetic, reproducible).

Daily orders across five categories and five Egyptian regions with seasonal
uplift (Ramadan / year-end peaks) and category-specific price ranges.
"""
import random
import csv
from datetime import date, timedelta

random.seed(7)

CATEGORIES = {
    "Electronics": (500, 5000),
    "Clothing": (150, 1200),
    "Home & Kitchen": (200, 2500),
    "Books": (80, 400),
    "Sports": (100, 1500),
}
REGIONS = ["Cairo", "Alexandria", "Giza", "Mansoura", "Aswan"]
REGION_WEIGHTS = [0.38, 0.22, 0.18, 0.12, 0.10]
PAYMENTS = ["Credit Card", "Cash", "Mobile Wallet", "Bank Transfer"]
PAYMENT_WEIGHTS = [0.35, 0.30, 0.25, 0.10]


def seasonal_factor(d):
    """Higher sales in Ramadan-ish spring weeks and November-December."""
    factor = 1.0
    if d.month in (3, 4):
        factor *= 1.35
    if d.month in (11, 12):
        factor *= 1.5
    if d.month in (6, 7):
        factor *= 0.85
    return factor


def main():
    start = date(2024, 1, 1)
    rows = []
    order_id = 1
    for day_offset in range(730):
        day = start + timedelta(days=day_offset)
        base_orders = random.randint(2, 6)
        n_orders = max(1, round(base_orders * seasonal_factor(day)))
        for _ in range(n_orders):
            category = random.choice(list(CATEGORIES))
            lo, hi = CATEGORIES[category]
            price = round(random.uniform(lo, hi), 2)
            quantity = random.choices([1, 2, 3, 4, 5], weights=[50, 25, 12, 8, 5])[0]
            rows.append({
                "order_id": f"SO-{order_id:06d}",
                "order_date": day.isoformat(),
                "customer_id": f"CUST-{random.randint(1, 1800):04d}",
                "category": category,
                "region": random.choices(REGIONS, weights=REGION_WEIGHTS)[0],
                "quantity": quantity,
                "unit_price": price,
                "payment_method": random.choices(PAYMENTS, weights=PAYMENT_WEIGHTS)[0],
                "total_amount": round(quantity * price, 2),
            })
            order_id += 1

    with open("data/sales_data.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} orders to data/sales_data.csv")


if __name__ == "__main__":
    main()
