{{ config(materialized='table') }}

WITH detections AS (
    SELECT
        message_id::BIGINT AS message_id,
        LOWER(channel_name) AS channel_name,
        image_path,
        detected_class,
        confidence_score::FLOAT AS confidence_score,
        image_category
    FROM raw.image_detections
    WHERE message_id ~ '^[0-9]+$'
),

joined AS (
    SELECT
        MD5(
            detections.channel_name || '-' ||
            detections.message_id || '-' ||
            detections.detected_class || '-' ||
            detections.confidence_score
        ) AS detection_key,

        detections.message_id,
        fct_messages.channel_key,
        fct_messages.date_key,
        detections.detected_class,
        detections.confidence_score,
        detections.image_category,
        detections.image_path

    FROM detections
    JOIN {{ ref('dim_channels') }} AS dim_channels
        ON detections.channel_name = LOWER(dim_channels.channel_name)

    JOIN {{ ref('fct_messages') }} AS fct_messages
        ON detections.message_id = fct_messages.message_id
       AND dim_channels.channel_key = fct_messages.channel_key
)

SELECT *
FROM joined