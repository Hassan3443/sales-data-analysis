# Customer Insights

- **1,510 customers**, 7,114,542 EGP total revenue
- **Top 20% of customers generate 53% of revenue** (Pareto curve in `figures/pareto_customers.png`)
- Average cohort retention: **7.1%** order again one month after first purchase, **6.5%** after three months

## RFM segments

| Segment | Customers | % of customers | Revenue (EGP) | % of revenue |
| --- | ---: | ---: | ---: | ---: |
| Champions | 126 | 8.3% | 1,215,285 | 17.1% |
| Loyal | 39 | 2.6% | 346,744 | 4.9% |
| Potential Loyalist | 335 | 22.2% | 1,939,311 | 27.3% |
| New Customers | 327 | 21.7% | 1,178,947 | 16.6% |
| At Risk | 207 | 13.7% | 1,652,179 | 23.2% |
| Hibernating | 476 | 31.5% | 782,075 | 11.0% |

Scores: Recency (days since last order, lower is better), Frequency (orders), Monetary (revenue), each scored 1-5 (quintiles for R and M, fixed bands for F: 1, 2, 3, 4, 5+ orders). Segment rules live in `assign_segment` in `src/customer_analysis.py`.

## What to do with it

1. **Champions and Loyal:** protect them with early access and loyalty perks; they carry a disproportionate share of revenue.
2. **At Risk:** high past value but gone quiet. A win-back offer here has the best return per message sent.
3. **New Customers:** a second purchase within 30-60 days is what turns them into Loyal customers; trigger a follow-up offer.
4. **Hibernating:** low value and inactive. Cheap, automated re-engagement only.
