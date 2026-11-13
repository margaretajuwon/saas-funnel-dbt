-- Rates are probabilities; counts must nest (activated, converted <= signups).
select * from {{ ref('fct_funnel') }}
where activation_rate not between 0 and 1 or signup_to_paid_rate not between 0 and 1
   or activated > signups or converted_to_paid > signups
