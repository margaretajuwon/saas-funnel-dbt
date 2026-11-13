-- End-of-month MRR per account. Grain: account_id x month_end.
with months as (
    select cast(range as date) as month_end
    from range(date '2023-01-31', date '2025-07-01', interval 1 month)
),
seg as (
    select * from {{ ref('stg_subscriptions') }}
)
select s.account_id, last_day(m.month_end) as month_end, sum(s.mrr) as mrr
from months m
join seg s on s.start_date <= last_day(m.month_end) and (s.end_date is null or s.end_date > last_day(m.month_end))
where last_day(m.month_end) <= date '2025-06-30'
group by 1, 2
