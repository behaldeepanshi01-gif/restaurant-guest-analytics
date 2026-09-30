"""
Restaurant Guest Analytics: data generator

The restaurant: an upscale, 90-seat dinner restaurant with a bar in New York
City, modeled on the kind of place I worked as a Customer Analytics Analyst.
All data is SIMULATED. No real restaurant's data or name is used.

The story the data holds (and the SQL has to find):
  Weeks 1-8   Buzz builds. Reservations and covers climb every week, but the
              floor team stays the same size. Peak-night service slows down and
              guest ratings slip, even though the room is fuller than ever.
  Week 6      A new beverage menu with higher spirit prices is approved, but the
              POS back end is never updated for spirits. Servers ring cocktails
              and pours at the OLD prices.
  Week 9      Analyst starts. Weeks 9-10: reviews 500+ guest data points a
              month, finds where and why ratings drop, and while loading the
              next menu update into the POS, finds the stale spirit prices.
  Week 11     Fixes go live: one more server and one more bartender on peak
              nights, reservation pacing capped per 15-minute slot, and correct
              spirit prices in the POS.
  Weeks 11-16 Service speeds up, ratings recover, spirits are charged right.

Run:  python scripts/generate_data.py
Out:  data/service_nights.csv, data/guest_feedback.csv,
      data/bar_pos_sales.csv, data/beverage_price_list.csv
"""
import numpy as np
import pandas as pd
from pathlib import Path

SEED = 7
rng = np.random.default_rng(SEED)
ROOT = Path(__file__).resolve().parents[1]

WEEKS = 16
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
SEATS = 90
FIX_WEEK = 11                   # staffing + pacing + POS fix go live
STALE_FROM, STALE_TO = 6, 10    # spirits charged at old prices in these weeks

# ---------------------------------------------------------------------------
# 1. Service nights: demand, staffing, service speed
# ---------------------------------------------------------------------------
BASE_COVERS = {"Mon": 95, "Tue": 110, "Wed": 125, "Thu": 150, "Fri": 205, "Sat": 220, "Sun": 150}
PEAK = {"Fri", "Sat"}

nights = []
for w in range(1, WEEKS + 1):
    buzz = 1 + 0.035 * min(w, 10)                      # demand grows ~3.5%/week, then holds
    for d in DAYS:
        peak = d in PEAK or d == "Thu"
        covers = int(rng.poisson(BASE_COVERS[d] * buzz))
        reservations = int(covers * rng.uniform(0.72, 0.82))
        walk_ins = covers - reservations
        waitlist = int(rng.poisson(max(covers - 180, 0) * 0.6 + 3))
        # staffing: flat before the fix, +1 server and +1 bartender on peak nights after
        servers = 7 if d in PEAK else (6 if d == "Thu" else 5)
        bartenders = 2 if peak else 1
        if w >= FIX_WEEK:                              # staff to forecast covers
            servers = max(servers, int(np.ceil(covers / 30)))
            bartenders = max(bartenders, int(np.ceil(covers / 120)))
        covers_per_server = covers / servers
        # service speed: minutes from order to food; drink wait at the bar
        ticket = 15 + 0.9 * max(covers_per_server - 27, 0) + rng.normal(0, 1.5)
        if w >= FIX_WEEK:                              # reservation pacing smooths the rush
            ticket -= 1.5 if peak else 0.5
        drink_wait = 4 + 0.06 * max(covers / bartenders - 80, 0) + rng.normal(0, 0.8)
        nights.append(dict(week=w, day=d, peak_night=int(peak), covers=covers,
                           reservations=reservations, walk_ins=walk_ins, waitlist=waitlist,
                           servers=servers, bartenders=bartenders,
                           covers_per_server=round(covers_per_server, 1),
                           avg_ticket_minutes=round(max(ticket, 11), 1),
                           avg_drink_wait_minutes=round(max(drink_wait, 3), 1)))
nights = pd.DataFrame(nights)

# ---------------------------------------------------------------------------
# 2. Beverage menu and bar POS sales (spirits pricing issue)
# ---------------------------------------------------------------------------
BEV = pd.DataFrame([
    # item,                     category,   mix,  old, new (approved week 6)
    ("House Old Fashioned",     "Spirits",  .14, 17, 19),
    ("Mango Chili Margarita",   "Spirits",  .16, 16, 18),
    ("Cardamom Gin & Tonic",    "Spirits",  .12, 16, 17),
    ("Whiskey (pour)",          "Spirits",  .10, 15, 16),
    ("Tequila (pour)",          "Spirits",  .07, 14, 15),
    ("Espresso Martini",        "Spirits",  .09, 18, 20),
    ("House Red (glass)",       "Wine",     .10, 15, 16),
    ("House White (glass)",     "Wine",     .09, 14, 15),
    ("Lager",                   "Beer",     .08,  9, 10),
    ("Mango Lassi",             "Zero-proof", .05, 9, 10),
], columns=["item", "category", "mix", "price_old", "price_new"])
DRINKS_PER_COVER = 1.15

bar = []
for n in nights.itertuples(index=False):
    units = rng.poisson(n.covers * DRINKS_PER_COVER * BEV.mix.values)
    for b, u in zip(BEV.itertuples(index=False), units):
        if u == 0:
            continue
        approved = b.price_new if n.week >= STALE_FROM else b.price_old
        stale = b.category == "Spirits" and STALE_FROM <= n.week <= STALE_TO
        charged = b.price_old if stale else approved
        bar.append((n.week, n.day, b.item, b.category, int(u), charged, round(u * charged, 2)))
bar = pd.DataFrame(bar, columns=["week", "day", "item", "category", "units",
                                 "pos_unit_price", "pos_revenue"])

price_list = pd.concat([
    BEV.assign(price=BEV.price_old, effective_from_week=1, effective_to_week=STALE_FROM - 1),
    BEV.assign(price=BEV.price_new, effective_from_week=STALE_FROM, effective_to_week=99),
])[["item", "category", "price", "effective_from_week", "effective_to_week"]]

# food + drinks check per cover (drinks from POS, food simulated)
bar_rev = bar.groupby(["week", "day"]).pos_revenue.sum().rename("bev_revenue")
nights = nights.merge(bar_rev, on=["week", "day"])
nights["food_revenue"] = (nights.covers * rng.normal(68, 4, len(nights))).round(2)
nights["total_revenue"] = (nights.food_revenue + nights.bev_revenue).round(2)

# ---------------------------------------------------------------------------
# 3. Guest feedback: ~130 responses a week (500+ a month)
# ---------------------------------------------------------------------------
TOPICS = ["Wait time", "Service speed", "Food quality", "Drinks", "Ambience", "Value"]
SOURCES = ["Post-visit survey", "Google", "Resy", "Instagram DM"]

fb = []
fid = 0
for n in nights.itertuples(index=False):
    k = int(rng.poisson(n.covers * 0.11))              # ~11% of covers leave feedback
    for _ in range(k):
        fid += 1
        # how the evening felt, driven by real service conditions that night
        slow = max(n.avg_ticket_minutes - 17, 0) * 0.115 + max(n.avg_drink_wait_minutes - 5, 0) * 0.105
        score = 4.6 - slow + rng.normal(0, 0.55)
        rating = int(np.clip(round(score), 1, 5))
        # what they talk about: slow nights produce wait / speed complaints
        p = np.array([0.08 + slow * 0.30, 0.08 + slow * 0.25, 0.30, 0.16, 0.24, 0.10])
        topic = rng.choice(TOPICS, p=p / p.sum())
        sentiment = "Positive" if rating >= 4 else ("Neutral" if rating == 3 else "Negative")
        fb.append((fid, n.week, n.day, rng.choice(SOURCES, p=[.45, .30, .18, .07]),
                   rating, topic, sentiment))
fb = pd.DataFrame(fb, columns=["feedback_id", "week", "day", "source", "rating", "topic", "sentiment"])

# ---------------------------------------------------------------------------
# 4. Save
# ---------------------------------------------------------------------------
nights.to_csv(ROOT / "data" / "service_nights.csv", index=False)
fb.to_csv(ROOT / "data" / "guest_feedback.csv", index=False)
bar.to_csv(ROOT / "data" / "bar_pos_sales.csv", index=False)
price_list.to_csv(ROOT / "data" / "beverage_price_list.csv", index=False)
print(f"service_nights:  {len(nights)} nights over {WEEKS} weeks | {nights.covers.sum():,} covers")
print(f"guest_feedback:  {len(fb):,} responses (~{len(fb) / WEEKS * 4.33:,.0f} a month)")
print(f"bar_pos_sales:   {len(bar):,} rows")
