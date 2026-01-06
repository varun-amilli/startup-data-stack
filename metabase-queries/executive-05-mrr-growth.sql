-- ============================================
-- Dashboard: Executive Dashboard
-- Card: MRR Over Time
-- Visualization: Line Chart (X: month, Y: total_mrr)
-- ============================================

SELECT 
    month,
    total_mrr,
    paying_customers
FROM analytics.fct_mrr_by_month
ORDER BY month;
