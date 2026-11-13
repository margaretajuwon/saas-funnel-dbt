"""Read the dbt marts, make charts, and write README.md with the real numbers. Run after: dbt build --profiles-dir ."""
from pathlib import Path
import duckdb, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).parent
RES = HERE / "results"; RES.mkdir(exist_ok=True)
con = duckdb.connect(str(HERE / "warehouse.duckdb"), read_only=True)

ch = con.execute("""select acquisition_channel, sum(signups) signups, sum(activated) activated, sum(converted_to_paid) paid,
    round(sum(activated)*100.0/sum(signups),1) act_pct, round(sum(converted_to_paid)*100.0/sum(signups),1) paid_pct
    from fct_funnel group by 1 order by paid_pct desc""").df()
ret = con.execute("select month_end, net_revenue_retention*100 nrr, gross_revenue_retention*100 grr from fct_revenue_retention order by 1").df()
br = con.execute("select * from fct_mrr_bridge order by month_end").df()
last = ret.iloc[-1]
mrr_end = br.closing_mrr.iloc[-1]

fig, ax = plt.subplots(figsize=(7, 3.8))
ax.bar(ch.acquisition_channel, ch.act_pct, label="Activated", color="#a0aec0")
ax.bar(ch.acquisition_channel, ch.paid_pct, label="Signup to paid", color="#2b6cb0")
ax.set_ylabel("% of signups"); ax.set_title("Funnel conversion by acquisition channel"); ax.legend()
plt.tight_layout(); plt.savefig(RES / "funnel_by_channel.png", dpi=140); plt.close()

fig, ax = plt.subplots(figsize=(7, 3.8))
ax.plot(ret.month_end, ret.nrr, label="Net revenue retention (T12M)", color="#2b6cb0")
ax.plot(ret.month_end, ret.grr, label="Gross revenue retention (T12M)", color="#a0aec0")
ax.axhline(100, color="k", lw=0.7); ax.set_ylabel("%"); ax.set_title("Revenue retention"); ax.legend()
plt.tight_layout(); plt.savefig(RES / "revenue_retention.png", dpi=140); plt.close()

fig, ax = plt.subplots(figsize=(7, 3.8))
ax.stackplot(br.month_end, br.new_mrr, br.expansion_mrr, labels=["New", "Expansion"], colors=["#2b6cb0", "#68a0d8"])
ax.stackplot(br.month_end, br.contraction_mrr, br.churned_mrr, labels=["Contraction", "Churn"], colors=["#f6ad55", "#e53e3e"])
ax.axhline(0, color="k", lw=0.7); ax.set_ylabel("MRR movement ($)"); ax.set_title("MRR bridge by month"); ax.legend(ncol=2, fontsize=8)
plt.tight_layout(); plt.savefig(RES / "mrr_bridge.png", dpi=140); plt.close()

tbl = "| channel | signups | activated | paid | activated % | signup to paid % |\n|---|---|---|---|---|---|\n" + "\n".join(
    f"| {r.acquisition_channel} | {int(r.signups):,} | {int(r.activated):,} | {int(r.paid):,} | {r.act_pct} | {r.paid_pct} |" for r in ch.itertuples())
best, worst = ch.iloc[0], ch.iloc[-1]

readme = f"""# SaaS funnel and revenue model in dbt (DuckDB)

**Synthetic data, real method.** A product-led-growth SaaS company is simulated (6,000 accounts, 2023-01 to 2025-06, fixed seed;
no employer data). The point is the analytics-engineering workflow: staged sources, tested marts with a documented grain,
and metrics a growth or finance team can trust.

## What is in the project
| layer | model | grain |
|---|---|---|
| staging | `stg_accounts`, `stg_events`, `stg_subscriptions` | one row per account / event / subscription segment |
| mart | `fct_funnel` | signup month x acquisition channel (signups, activated, paid) |
| mart | `fct_account_mrr_monthly` | account x month-end MRR |
| mart | `fct_mrr_bridge` | month: new + expansion + contraction + churn = closing - opening |
| mart | `fct_revenue_retention` | month: trailing-12-month net (NRR) and gross (GRR) revenue retention |

**Tests (15 data tests, all pass):** uniqueness and not-null on keys, `accepted_values` on channel, a `relationships`
test from subscriptions to accounts, and three singular tests: the MRR bridge must reconcile every month, funnel counts must nest
(activated and paid never exceed signups), and GRR can never exceed 1 or NRR.

**Definitions (written down on purpose).** Activated = created a project AND invited a teammate within 7 days of signup.
MRR is measured on the last day of each month. GRR caps each account at its starting MRR, so expansion cannot hide churn.

## Results
Channels, ranked by signup-to-paid conversion:

{tbl}

- **{best.acquisition_channel}** converts best ({best.paid_pct}% of signups to paid); **{worst.acquisition_channel}** converts worst ({worst.paid_pct}%).
  Optimizing for signup volume alone would over-fund the weakest channel.
- Closing MRR at 2025-06: **${mrr_end:,.0f}**. Trailing-12-month **NRR {last.nrr:.1f}%**, **GRR {last.grr:.1f}%**.
  An NRR {'above' if last.nrr > 100 else 'below'} 100% means {'expansion more than offsets churn' if last.nrr > 100 else 'churn outweighs expansion'}.

![funnel](results/funnel_by_channel.png)
![retention](results/revenue_retention.png)
![bridge](results/mrr_bridge.png)

## Caveats I would raise on a real project
- Synthetic activation and churn rates are assumptions, so the absolute numbers are illustrative; the workflow is the deliverable.
- Activation is defined within 7 days. A longer window or a different qualifying event changes channel ranking; in practice I would test that against paid conversion.
- No seasonality or pricing changes are modeled.

## Run it
```
pip install duckdb dbt-duckdb pandas matplotlib numpy
python generate_data.py
dbt build --profiles-dir .
python analyze.py
```
"""
(HERE / "README.md").write_text(readme, encoding="utf-8")
print(ch.to_string(index=False)); print(last.to_dict(), mrr_end)

