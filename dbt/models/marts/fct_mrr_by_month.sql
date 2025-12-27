-- Revenue data comes from Stripe (source of truth for payments)
WITH subscriptions AS (
    SELECT * FROM {{ ref('stg_stripe_subscriptions') }}
),

months AS (
    SELECT 
        DATE_TRUNC('month', created_at)::DATE AS month
    FROM subscriptions
    WHERE created_at IS NOT NULL
    UNION
    SELECT 
        DATE_TRUNC('month', CURRENT_DATE)::DATE AS month
),

month_series AS (
    SELECT DISTINCT month 
    FROM months
    WHERE month IS NOT NULL
),

subscription_months AS (
    SELECT
        m.month
        , s.stripe_subscription_id
        , s.stripe_customer_id
        , s.plan_id
        , s.mrr
        , s.created_at
        , s.canceled_at
    FROM month_series m
    CROSS JOIN subscriptions s
    WHERE DATE_TRUNC('month', s.created_at)::DATE <= m.month
      AND (s.canceled_at IS NULL OR DATE_TRUNC('month', s.canceled_at)::DATE > m.month)
)

SELECT
    month
    , COUNT(DISTINCT stripe_subscription_id) AS active_subscriptions
    , COUNT(DISTINCT stripe_customer_id) AS paying_customers
    , SUM(mrr) AS total_mrr
    , AVG(mrr) AS avg_mrr_per_customer
    
    -- By plan
    , SUM(CASE WHEN plan_id = 'starter' THEN mrr ELSE 0 END) AS mrr_starter
    , SUM(CASE WHEN plan_id = 'professional' THEN mrr ELSE 0 END) AS mrr_professional
    , SUM(CASE WHEN plan_id = 'enterprise' THEN mrr ELSE 0 END) AS mrr_enterprise

FROM subscription_months
GROUP BY month
ORDER BY month
