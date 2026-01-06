-- ============================================
-- Dashboard: Executive Dashboard
-- Card: Key Metrics Summary
-- Visualization: Table
-- ============================================

SELECT 
    'Total Users' as metric,
    COUNT(*)::text as value
FROM analytics.fct_user_metrics

UNION ALL

SELECT 
    'Activated Users',
    COUNT(*)::text
FROM analytics.fct_user_metrics 
WHERE is_activated = true

UNION ALL

SELECT 
    'Paying Customers',
    COUNT(*)::text
FROM analytics.fct_user_metrics 
WHERE is_paying = true

UNION ALL

SELECT 
    'Total MRR',
    '$' || ROUND(SUM(current_mrr))::text
FROM analytics.fct_user_metrics 
WHERE is_paying = true

UNION ALL

SELECT 
    'Avg MRR per Customer',
    '$' || ROUND(AVG(current_mrr), 2)::text
FROM analytics.fct_user_metrics 
WHERE is_paying = true;
