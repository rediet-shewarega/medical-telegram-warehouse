SELECT
    f.*
FROM {{ ref('fct_messages') }} f
JOIN {{ ref('dim_dates') }} d
    ON f.date_key = d.date_key
WHERE d.full_date > CURRENT_DATE
