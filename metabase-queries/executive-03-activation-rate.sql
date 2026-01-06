-- ============================================
-- Dashboard: Executive Dashboard
-- Card: Activation Rate
-- Visualization: Number (suffix with %)
-- ============================================

SELECT 
    ROUND(
        100.0 * SUM(CASE WHEN is_activated THEN 1 ELSE 0 END)::numeric / COUNT(*), 
        1
    ) as activation_rate_pct
FROM analytics.fct_user_metrics;
