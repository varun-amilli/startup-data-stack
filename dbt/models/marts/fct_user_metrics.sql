WITH users AS (
    SELECT * FROM {{ ref('stg_users') }}
),

events AS (
    SELECT * FROM {{ ref('stg_events') }}
),

stripe_customers AS (
    SELECT * FROM {{ ref('stg_stripe_customers') }}
),

stripe_subscriptions AS (
    SELECT * FROM {{ ref('stg_stripe_subscriptions') }}
),

user_event_summary AS (
    SELECT
        user_id
        , COUNT(*) AS total_events
        , COUNT(DISTINCT DATE_TRUNC('day', event_at)) AS active_days
        , MIN(event_at) AS first_event_at
        , MAX(event_at) AS last_event_at
    FROM events
    GROUP BY user_id
),

user_payment_summary AS (
    SELECT
        u.user_id
        , sc.stripe_customer_id
        , MAX(CASE WHEN ss.is_active THEN ss.mrr ELSE 0 END) AS current_mrr
        , MAX(CASE WHEN ss.is_active THEN ss.plan_id ELSE NULL END) AS current_plan
        , SUM(CASE WHEN ss.is_active THEN 1 ELSE 0 END) AS active_subscription_count
    FROM users u
    LEFT JOIN stripe_customers sc ON LOWER(u.email) = LOWER(sc.email)
    LEFT JOIN stripe_subscriptions ss ON sc.stripe_customer_id = ss.stripe_customer_id
    GROUP BY u.user_id, sc.stripe_customer_id
)

SELECT
    u.user_id
    , u.email
    , u.user_name
    , u.company
    , u.signup_at
    , u.activated_at
    , u.is_activated
    , u.days_to_activate
    
    -- Event metrics (from TaskFlow)
    , COALESCE(e.total_events, 0) AS total_events
    , COALESCE(e.active_days, 0) AS active_days
    , e.first_event_at
    , e.last_event_at
    
    -- Payment metrics (from Stripe - source of truth)
    , p.stripe_customer_id
    , COALESCE(p.current_mrr, 0) AS current_mrr
    , p.current_plan
    , COALESCE(p.active_subscription_count, 0) > 0 AS is_paying
    
    -- Engagement score (based on TaskFlow events)
    , CASE
        WHEN e.active_days >= 20 THEN 'high'
        WHEN e.active_days >= 5 THEN 'medium'
        WHEN e.active_days > 0 THEN 'low'
        ELSE 'none'
    END AS engagement_level

FROM users u
LEFT JOIN user_event_summary e ON u.user_id = e.user_id
LEFT JOIN user_payment_summary p ON u.user_id = p.user_id
