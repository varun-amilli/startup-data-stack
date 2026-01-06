-- ============================================
-- Dashboard: Executive Dashboard
-- Card: Activation Funnel
-- Visualization: Funnel Chart
-- ============================================

SELECT 
    funnel_step,
    user_count
FROM analytics.fct_activation_funnel
ORDER BY funnel_step;
