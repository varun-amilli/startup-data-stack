WITH source AS (
    SELECT * FROM {{ source('taskflow', 'users') }}
)

SELECT
    id AS user_id,
    email,
    name AS user_name,
    company,
    created_at AS signup_at,
    activated_at,
    plan,
    activated_at IS NOT NULL AS is_activated,
    EXTRACT(DAY FROM (activated_at - created_at)) AS days_to_activate
FROM source
