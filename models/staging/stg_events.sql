select account_id, cast(event_at as date) as event_date, event_name
from {{ source('raw','events') }}
