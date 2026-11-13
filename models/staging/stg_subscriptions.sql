select account_id, cast(start_date as date) as start_date, cast(end_date as date) as end_date, plan, mrr
from {{ source('raw','subscriptions') }}
