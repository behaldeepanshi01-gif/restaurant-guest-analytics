# Restaurant Guest Analytics

**The room was fuller than ever. Guests were less happy than ever. Why, and what was it costing?**

As a Customer Analytics Analyst at an upscale restaurant in New York City, I worked through 500+ guest data points a month and found a gap: engagement was rising, but satisfaction was slipping. Busy nights had outgrown the floor team, and service was slowing down right when the room was fullest. Staffing changes lifted satisfaction scores 22%. While loading a new beverage menu and pricing, I also found that spirit prices had never been updated in the POS back end. Servers were ringing drinks at the old prices, and it had cost about $8,000 before I caught and fixed it.

This project rebuilds both analyses in SQL on simulated data I can share publicly. **No real restaurant's data or name is used.**

![SQL](https://img.shields.io/badge/SQL-SQLite-4479A1?style=flat)
![Python](https://img.shields.io/badge/Python-pandas-3776AB?style=flat)
![Tableau]   [![Tableau](https://img.shields.io/badge/Tableau-dashboard-E97627?style=flat)](https://public.tableau.com/app/profile/deepanshi.behal5790/viz/RestaurantGuestAnalytics/GuestAnalytics)

---

## The restaurant (simulated)

An upscale 90-seat dinner restaurant with a bar in NYC, over 16 weeks:

| Weeks | What happens |
|---|---|
| 1 to 8 | Buzz builds. Covers and reservations climb about 3.5% a week, but the floor team stays the same size. |
| 6 | A new beverage menu with higher spirit prices is approved. The POS back end is **not** updated for spirits. |
| 9 to 10 | The analysis: 500+ guest responses a month, matched to how busy each night was and how fast service ran. |
| 11 | Fixes go live: staff each night to forecast covers (about 30 covers per server), cap reservations per slot, and correct the spirit prices in the POS. |
| 12 to 16 | Measure the result. |

**Data:** 112 service nights, 20,991 covers, 2,333 guest responses (about 630 a month, from a post-visit survey, Google, Resy and Instagram), and 1,120 rows of item-level bar POS sales. Seed = 7, so results are reproducible.

---

## What the analysis found

**1. Engagement up, satisfaction down (Q1).** From week 1 to week 10, weekly covers rose 32% (1,086 to 1,429) and the waitlist nearly tripled (64 to 184). Over the same weeks, average rating fell from 4.19 to 3.43, and the share of 4 and 5 star ratings fell from 78% to 42%.

**2. The rating breaks at about 30 covers per server (Q2).**

| Covers per server | Avg ticket time | Avg rating |
|---|---|---|
| Up to 26 | 14.6 min | 4.51 |
| 26 to 30 | 15.1 min | 4.50 |
| 30 to 34 | 19.0 min | 4.21 |
| Over 34 | 25.2 min | **3.35** |

Food wasn't the problem. Service speed at peak was.

**3. Unhappy guests were talking about waiting (Q3).** Before the fix, 53% of 1 to 3 star reviews were about wait time or service speed. After, it was about 12%.

**4. The fix lifted satisfaction 22% (Q4).**

| | Before (wk 7-10) | After (wk 12-16) |
|---|---|---|
| Covers per night | 195 | 203 |
| Covers per server | 33.6 | 27.5 |
| Ticket time | 21.1 min | 15.0 min |
| Drink wait | 7.6 min | 4.7 min |
| **Avg rating** | **3.72** | **4.52 (+22%)** |

Busier *and* happier: the room served more covers after the fix, not fewer.

**5. The POS was undercharging every spirit, about $8,200 in five weeks (Q5, Q6).** From week 6, the approved price list had the new spirit prices, but the POS kept charging the old ones: about $1,600 a week across 5,200+ drinks. Wine, beer and zero-proof drinks were charged correctly, and that pattern is what points to one missed table in the back end rather than a pricing mistake across the menu. The biggest gaps were the Mango Chili Margarita ($16 charged vs $18 approved) and the House Old Fashioned ($17 vs $19).

**6. The pricing fix paid for 43% of the extra staff (Q7).** Staffing to demand added about $15,400 in labor every four weeks. Charging spirits correctly brought back about $6,600 over the same four weeks. Fixing the POS covered almost half of what it cost to fix the guest experience.

---

## How it's built

```
scripts/generate_data.py      builds the 16 weeks (every assumption is commented)
   │
   ▼
data/service_nights.csv       one row per night: covers, reservations, staff, service times, revenue
data/guest_feedback.csv       one row per guest response: rating, topic, source
data/bar_pos_sales.csv        one row per night and drink: units, price the POS charged
data/beverage_price_list.csv  approved drink prices, with the week they took effect
   │
   ▼  sql/01_schema.sql, sql/02_analysis.sql   (run with scripts/run_sql.py)
output/Q1..Q7.csv             query results, ready for Tableau
```

| Query | Question |
|---|---|
| Q1 | Week by week: is the room getting fuller while guests get less happy? |
| Q2 | At how many covers per server does the rating break? |
| Q3 | What are unhappy guests talking about, before and after? |
| Q4 | Before vs after the fix |
| Q5 | Is the bar POS charging the approved price? Weekly gap |
| Q6 | Which drinks? |
| Q7 | What did the fixes cost, and what did they bring back? |

## Run it

```bash
pip install pandas numpy
python scripts/generate_data.py
python scripts/run_sql.py
```

## Limits (said plainly)

- All data is simulated to recreate what I saw. The size of every effect comes from the assumptions in `generate_data.py`. The value is the method.
- Labor cost per shift is an assumption ($220 per server, $240 per bartender).
- The next step on real systems: join reservation-platform data, POS checks and guest reviews by date and service time, and refresh weekly.

---

**Deepanshi Behal** · [Portfolio](https://behaldeepanshi01-gif.github.io) · [LinkedIn](https://linkedin.com/in/bdeepanshi) · [GitHub](https://github.com/behaldeepanshi01-gif)
