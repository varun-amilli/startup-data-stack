WITH users AS (
    SELECT * FROM {{ ref('stg_users') }}
),

stripe_customers AS (
    SELECT * FROM {{ ref('stg_stripe_customers') }}
),

stripe_subscriptions AS (
    SELECT * FROM {{ ref('stg_stripe_subscriptions') }}
),

user_payment_status AS (
    SELECT 
        u.user_id,
        MAX(CASE WHEN ss.is_active THEN 1 ELSE 0 END) AS has_paid_subscription
    FROM users u
    LEFT JOIN stripe_customers sc ON LOWER(u.email) = LOWER(sc.email)
    LEFT JOIN stripe_subscriptions ss ON sc.stripe_customer_id = ss.stripe_customer_id
    GROUP BY u.user_id
),

daily_signups AS (
    SELECT
        DATE_TRUNC('day', signup_at)::DATE AS signup_date,
        COUNT(*) AS signups,
        SUM(CASE WHEN is_activated THEN 1 ELSE 0 END) AS activated,
        SUM(CASE WHEN p.has_paid_subscription = 1 THEN 1 ELSE 0 END) AS converted_to_paid,
        AVG(days_to_activate) FILTER (WHERE is_activated) AS avg_days_to_activate
    FROM users u
    LEFT JOIN user_payment_status p ON u.user_id = p.user_id
    GROUP BY DATE_TRUNC('day', signup_at)::DATE
)

SELECT
    signup_date,
    signups,
    activated,
    converted_to_paid,
    
    -- Conversion rates
    ROUND(100.0 * activated / NULLIF(signups, 0), 2) AS activation_rate,
    ROUND(100.0 * converted_to_paid / NULLIF(activated, 0), 2) AS activation_to_paid_rate,
    ROUND(100.0 * converted_to_paid / NULLIF(signups, 0), 2) AS signup_to_paid_rate,
    
    ROUND(avg_days_to_activate, 1) AS avg_days_to_activate

FROM daily_signups
WHERE signup_date IS NOT NULL
ORDER BY signup_date DESC
