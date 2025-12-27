WITH stripe_subs AS (
    SELECT * FROM {{ ref('stg_stripe_subscriptions') }}
),

stripe_customers AS (
    SELECT * FROM {{ ref('stg_stripe_customers') }}
),

taskflow_users AS (
    SELECT * FROM {{ ref('stg_users') }}
)

SELECT
    u.user_id
    , u.email
    , u.user_name
    , u.company
    , sc.stripe_customer_id
    , s.stripe_subscription_id
    , s.plan_id
    , s.mrr
    , s.status
    , s.created_at AS subscription_start_date
    , s.canceled_at AS subscription_end_date
    , EXTRACT(DAY FROM (COALESCE(s.canceled_at, CURRENT_DATE) - s.created_at)) AS subscription_days
    , u.signup_at
    , EXTRACT(DAY FROM (s.created_at - u.signup_at)) AS days_to_subscribe
FROM taskflow_users u
LEFT JOIN stripe_customers sc ON LOWER(u.email) = LOWER(sc.email)
LEFT JOIN stripe_subs s ON sc.stripe_customer_id = s.stripe_customer_id
WHERE s.stripe_subscription_id IS NOT NULL  -- Only users with subscriptions
