WITH source AS (
    SELECT * FROM {{ source('stripe', 'subscriptions') }}
)

SELECT
    id AS stripe_subscription_id
    , customer_id AS stripe_customer_id
    , status
    , plan_id
    , ( plan_amount / 100.0 ) AS mrr
    , plan_currency
    , plan_interval
    , TO_TIMESTAMP(created) AS created_at
    , TO_TIMESTAMP(canceled_at) AS canceled_at
    , CASE WHEN status = 'active' THEN TRUE ELSE FALSE END AS is_active
FROM source
