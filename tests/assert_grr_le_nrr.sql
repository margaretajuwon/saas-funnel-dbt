-- GRR can never exceed 1 or exceed NRR.
select * from {{ ref('fct_revenue_retention') }}
where gross_revenue_retention > 1 or gross_revenue_retention > net_revenue_retention
