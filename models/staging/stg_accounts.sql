select account_id, cast(created_at as date) as signup_date,
       date_trunc('month', created_at)::date as signup_month, acquisition_channel, country
from {{ source('raw','accounts') }}
