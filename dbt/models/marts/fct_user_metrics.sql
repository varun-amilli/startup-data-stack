WITH users AS (
    SELECT * FROM {{ ref('stg_users') }}
),

subscriptions AS (
    SELECT * FROM {{ ref('stg_subscriptions') }}
),

events AS (
    SELECT * FROM {{ ref('stg_events') }}
),

user_event_summary AS (
    SELECT
        user_id,
        COUNT(*) AS total_events,
        COUNT(DISTINCT DATE_TRUNC('day', event_at)) AS active_days,
        MIN(event_at) AS first_event_at,
        MAX(event_at) AS last_event_at
    FROM events
    GROUP BY user_id
),

user_subscription_summary AS (
    SELECT
        user_id,
        MAX(CASE WHEN is_active THEN mrr ELSE 0 END) AS current_mrr,
        SUM(CASE WHEN is_active THEN 1 ELSE 0 END) AS active_subscription_count
    FROM subscriptions
    GROUP BY user_id
)

SELECT
    u.user_id,
    u.email,
    u.user_name,
    u.company,
    u.signup_at,
    u.activated_at,
    u.is_activated,
    u.days_to_activate,
    u.plan,
    
    -- Event metrics
    COALESCE(e.total_events, 0) AS total_events,
    COALESCE(e.active_days, 0) AS active_days,
    e.first_event_at,
    e.last_event_at,
    
    -- Subscription metrics
    COALESCE(s.current_mrr, 0) AS current_mrr,
    COALESCE(s.active_subscription_count, 0) > 0 AS is_paying,
    
    -- Engagement score
    CASE
        WHEN e.active_days >= 20 THEN 'high'
        WHEN e.active_days >= 5 THEN 'medium'
        WHEN e.active_days > 0 THEN 'low'
        ELSE 'none'
    END AS engagement_level

FROM users u
LEFT JOIN user_event_summary e ON u.user_id = e.user_id
LEFT JOIN user_subscription_summary s ON u.user_id = s.user_id
