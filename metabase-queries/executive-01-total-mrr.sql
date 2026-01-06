-- ============================================
-- Dashboard: Executive Dashboard
-- Card: Total MRR
-- Visualization: Number (Large, prefix with $)
-- ============================================

SELECT 
    ROUND(SUM(current_mrr)) as total_mrr
FROM analytics.fct_user_metrics 
WHERE is_paying = true;
