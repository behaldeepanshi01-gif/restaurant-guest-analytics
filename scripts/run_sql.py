"""Load the CSVs into SQLite, run every query in sql/02_analysis.sql,
print the results and save each one to output/ for Tableau.

Run:  python scripts/run_sql.py
"""
import sqlite3
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
con = sqlite3.connect(ROOT / "output" / "restaurant.db")
con.executescript((ROOT / "sql" / "01_schema.sql").read_text())
for t in ["service_nights", "guest_feedback", "bar_pos_sales", "beverage_price_list"]:
    pd.read_csv(ROOT / "data" / f"{t}.csv").to_sql(t, con, if_exists="append", index=False)

sql = (ROOT / "sql" / "02_analysis.sql").read_text()
blocks = [b.strip() for b in sql.split("\n-- Q") if "SELECT" in b]
pd.set_option("display.width", 200)
for b in blocks:
    title = b.splitlines()[0].lstrip("- ")
    query = "\n".join(l for l in b.splitlines()[1:] if not l.strip().startswith("--"))
    df = pd.read_sql(query, con)
    name = "Q" + title.split(".")[0]
    df.to_csv(ROOT / "output" / f"{name}.csv", index=False)
    print(f"\n=== Q{title} ===\n{df.to_string(index=False)}")
