-- Trailing-12-month net and gross revenue retention. Grain: month_end.
with base as (
    select account_id, month_end, mrr from {{ ref('fct_account_mrr_monthly') }}
),
months as (select distinct month_end from base)
select m.month_end,
       sum(t.mrr) as mrr_12m_ago,
       sum(coalesce(n.mrr, 0)) as mrr_now_from_same_accounts,
       round(sum(coalesce(n.mrr, 0)) * 1.0 / sum(t.mrr), 4) as net_revenue_retention,
       round(sum(least(coalesce(n.mrr, 0), t.mrr)) * 1.0 / sum(t.mrr), 4) as gross_revenue_retention
from months m
join base t on t.month_end = last_day(m.month_end - interval 12 month)
left join base n on n.account_id = t.account_id and n.month_end = m.month_end
group by m.month_end
