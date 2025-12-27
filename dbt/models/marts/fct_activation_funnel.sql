WITH users AS (
    SELECT * FROM {{ ref('stg_users') }}
),

daily_signups AS (
    SELECT
        DATE_TRUNC('day', signup_at)::DATE AS signup_date,
        COUNT(*) AS signups,
        SUM(CASE WHEN is_activated THEN 1 ELSE 0 END) AS activated,
        SUM(CASE WHEN plan IS NOT NULL THEN 1 ELSE 0 END) AS converted_to_paid,
        AVG(days_to_activate) FILTER (WHERE is_activated) AS avg_days_to_activate
    FROM users
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
