-- MRR bridge must reconcile: opening + movements = closing, every month.
select month_end
from {{ ref('fct_mrr_bridge') }}
where opening_mrr + new_mrr + expansion_mrr + contraction_mrr + churned_mrr <> closing_mrr
