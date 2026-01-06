-- ============================================
-- Dashboard: Executive Dashboard
-- Card: Paying Customers
-- Visualization: Number (Large)
-- ============================================

SELECT 
    COUNT(*) as paying_customers
FROM analytics.fct_user_metrics 
WHERE is_paying = true;
