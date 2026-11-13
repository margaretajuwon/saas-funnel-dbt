-- MRR bridge per month: new, expansion, contraction, churn. Grain: month_end.
with cur as (
    select account_id, month_end, mrr from {{ ref('fct_account_mrr_monthly') }}
),
prev as (
    select account_id, (month_end + interval 1 month)::date as month_end, mrr as prev_mrr from cur
),
joined as (
    select coalesce(c.account_id, p.account_id) as account_id,
           last_day(coalesce(c.month_end, p.month_end)) as month_end,
           coalesce(p.prev_mrr, 0) as prev_mrr, coalesce(c.mrr, 0) as mrr
    from cur c full outer join prev p on c.account_id = p.account_id and last_day(c.month_end) = last_day(p.month_end)
)
select month_end,
       sum(case when prev_mrr = 0 and mrr > 0 then mrr else 0 end) as new_mrr,
       sum(case when prev_mrr > 0 and mrr > prev_mrr then mrr - prev_mrr else 0 end) as expansion_mrr,
       sum(case when prev_mrr > 0 and mrr > 0 and mrr < prev_mrr then mrr - prev_mrr else 0 end) as contraction_mrr,
       sum(case when prev_mrr > 0 and mrr = 0 then -prev_mrr else 0 end) as churned_mrr,
       sum(prev_mrr) as opening_mrr, sum(mrr) as closing_mrr
from joined
where month_end <= date '2025-06-30'
group by 1
