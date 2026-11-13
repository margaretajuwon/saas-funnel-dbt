-- Funnel by signup month and channel. Grain: signup_month x acquisition_channel.
-- Activated = created a project AND invited a teammate within 7 days of signup.
with ev as (
    select a.account_id, a.signup_month, a.acquisition_channel,
           max(case when e.event_name = 'project_created' and e.event_date <= a.signup_date + 7 then 1 else 0 end) as did_project,
           max(case when e.event_name = 'teammate_invited' and e.event_date <= a.signup_date + 7 then 1 else 0 end) as did_invite
    from {{ ref('stg_accounts') }} a
    left join {{ ref('stg_events') }} e using (account_id)
    group by 1, 2, 3
),
paid as (
    select distinct account_id from {{ ref('stg_subscriptions') }}
)
select ev.signup_month, ev.acquisition_channel,
       count(*) as signups,
       sum(did_project * did_invite) as activated,
       count(paid.account_id) as converted_to_paid,
       round(sum(did_project * did_invite) * 1.0 / count(*), 4) as activation_rate,
       round(count(paid.account_id) * 1.0 / count(*), 4) as signup_to_paid_rate
from ev left join paid using (account_id)
group by 1, 2
