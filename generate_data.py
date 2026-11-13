"""Generate a SYNTHETIC B2B SaaS product-led-growth dataset into DuckDB (schema raw).
No employer data. Fixed seed. Run: python generate_data.py
Tables: raw.accounts, raw.events, raw.subscriptions
"""
from pathlib import Path
import duckdb, numpy as np, pandas as pd

rng = np.random.default_rng(42)
DB = Path(__file__).parent / "warehouse.duckdb"
N = 6000
START, CUTOFF = pd.Timestamp("2023-01-01"), pd.Timestamp("2025-06-30")

channels = ["organic", "paid_search", "paid_social", "referral", "outbound"]
ch_p = [0.30, 0.25, 0.15, 0.15, 0.15]
# channel quality: activation prob and trial->paid prob given activation
act = {"organic": .46, "paid_search": .38, "paid_social": .24, "referral": .55, "outbound": .42}
conv = {"organic": .34, "paid_search": .30, "paid_social": .20, "referral": .42, "outbound": .38}
plans = {"starter": 49, "team": 199, "business": 599}
plan_p = {"organic": [.6, .33, .07], "paid_search": [.55, .38, .07], "paid_social": [.75, .22, .03],
          "referral": [.45, .42, .13], "outbound": [.25, .45, .30]}
churn_m = {"starter": .035, "team": .02, "business": .011}   # monthly churn hazard
upgrade_m = {"starter": .03, "team": .02}

days = (CUTOFF - START).days
signup = START + pd.to_timedelta(rng.integers(0, days, N), unit="D")
ch = rng.choice(channels, N, p=ch_p)
acc = pd.DataFrame({"account_id": np.arange(1, N + 1), "created_at": signup, "acquisition_channel": ch,
                    "country": rng.choice(["US", "CA", "GB", "DE", "AU", "OTHER"], N, p=[.55, .08, .12, .08, .05, .12])})

events, subs = [], []
for a in acc.itertuples():
    events.append((a.account_id, a.created_at, "signed_up"))
    activated = rng.random() < act[a.acquisition_channel]
    if activated:
        d1 = a.created_at + pd.Timedelta(days=int(rng.integers(0, 4)))
        events.append((a.account_id, d1, "project_created"))
        if rng.random() < .8:
            events.append((a.account_id, d1 + pd.Timedelta(days=int(rng.integers(0, 4))), "teammate_invited"))
        for _ in range(int(rng.integers(1, 8))):
            events.append((a.account_id, d1 + pd.Timedelta(days=int(rng.integers(1, 40))), "core_action"))
    if activated and rng.random() < conv[a.acquisition_channel]:
        start = a.created_at + pd.Timedelta(days=int(rng.integers(7, 30)))
        if start > CUTOFF: continue
        plan = rng.choice(list(plans), p=plan_p[a.acquisition_channel])
        cur, t = start, start
        while True:
            # walk month by month
            nxt = t + pd.DateOffset(months=1)
            if nxt > CUTOFF:
                subs.append((a.account_id, cur, None, plan, plans[plan])); break
            if rng.random() < churn_m[plan]:
                subs.append((a.account_id, cur, nxt, plan, plans[plan])); break
            if plan in upgrade_m and rng.random() < upgrade_m[plan]:
                subs.append((a.account_id, cur, nxt, plan, plans[plan]))
                plan = "team" if plan == "starter" else "business"; cur = nxt
            t = nxt

ev = pd.DataFrame(events, columns=["account_id", "event_at", "event_name"])
ev = ev[ev.event_at <= CUTOFF]
sb = pd.DataFrame(subs, columns=["account_id", "start_date", "end_date", "plan", "mrr"])

con = duckdb.connect(str(DB))
con.execute("create schema if not exists raw")
for name, df in [("accounts", acc), ("events", ev), ("subscriptions", sb)]:
    con.execute(f"create or replace table raw.{name} as select * from df")
print({n: con.execute(f"select count(*) from raw.{n}").fetchone()[0] for n in ["accounts", "events", "subscriptions"]})
