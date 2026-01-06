-- Staging model for Stripe customers
-- Cleans and types the raw Stripe customer data

SELECT
    id AS stripe_customer_id
  , email
  , name
  , TO_TIMESTAMP(created) AS created_at
  , currency
  , delinquent
  , metadata

FROM {{ source('stripe', 'customers') }}
