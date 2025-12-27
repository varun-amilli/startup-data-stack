WITH source AS (
    SELECT * FROM {{ source('taskflow', 'subscriptions') }}
)

SELECT
    id AS subscription_id,
    user_id,
    stripe_subscription_id,
    plan,
    status,
    mrr_cents / 100.0 AS mrr,
    started_at,
    canceled_at,
    created_at,
    CASE 
        WHEN status = 'active' THEN TRUE 
        ELSE FALSE 
    END AS is_active
FROM source
