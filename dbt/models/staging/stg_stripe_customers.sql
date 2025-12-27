WITH source AS (
	SELECT * FROM {{ source('stripe', 'customers') }}
)

SELECT
	id as stripe_customer_id
	, email
	, name as customer_name
	, TO_TIMESTAMP(created) AS created_at
	, currency
	, company
	, industry
FROM source
