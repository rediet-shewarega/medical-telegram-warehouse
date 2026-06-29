SELECT
    *
FROM {{ ref('fct_messages') }}
WHERE view_count < 0
   OR forward_count < 0
