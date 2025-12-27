WITH source AS (
    SELECT * FROM {{ source('taskflow', 'events') }}
)

SELECT
    id AS event_id,
    user_id,
    event_name,
    event_properties,
    created_at AS event_at
FROM source
