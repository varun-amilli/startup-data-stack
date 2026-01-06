-- ============================================
-- Dashboard: Executive Dashboard
-- Card: Activated → Paying Conversion
-- Visualization: Number (suffix with %)
-- ============================================

SELECT 
    ROUND(
        100.0 * SUM(CASE WHEN is_paying THEN 1 ELSE 0 END)::numeric / 
        NULLIF(SUM(CASE WHEN is_activated THEN 1 ELSE 0 END), 0), 
        1
    ) as conversion_rate_pct
FROM analytics.fct_user_metrics;
