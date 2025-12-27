WITH subscriptions AS (
    SELECT * FROM {{ ref('stg_subscriptions') }}
),

-- Generate a series of months
months AS (
    SELECT 
        DATE_TRUNC('month', started_at)::DATE AS month
    FROM subscriptions
    WHERE started_at IS NOT NULL
    UNION
    SELECT 
        DATE_TRUNC('month', CURRENT_DATE)::DATE AS month
),

month_series AS (
    SELECT DISTINCT month 
    FROM months
    WHERE month IS NOT NULL
),

-- Calculate active subscriptions per month
subscription_months AS (
    SELECT
        m.month,
        s.subscription_id,
        s.user_id,
        s.plan,
        s.mrr,
        s.started_at,
        s.canceled_at
    FROM month_series m
    CROSS JOIN subscriptions s
    WHERE DATE_TRUNC('month', s.started_at)::DATE <= m.month
      AND (s.canceled_at IS NULL OR DATE_TRUNC('month', s.canceled_at)::DATE > m.month)
)

SELECT
    month,
    COUNT(DISTINCT subscription_id) AS active_subscriptions,
    COUNT(DISTINCT user_id) AS paying_customers,
    SUM(mrr) AS total_mrr,
    AVG(mrr) AS avg_mrr_per_customer,
    
    -- By plan
    SUM(CASE WHEN plan = 'starter' THEN mrr ELSE 0 END) AS mrr_starter,
    SUM(CASE WHEN plan = 'professional' THEN mrr ELSE 0 END) AS mrr_professional,
    SUM(CASE WHEN plan = 'enterprise' THEN mrr ELSE 0 END) AS mrr_enterprise

FROM subscription_months
GROUP BY month
ORDER BY month
