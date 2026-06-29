with source as (

    select
        message_id,
        channel_name,
        message_date,
        message_text,
        has_media,
        image_path,
        views,
        forwards,
        scrape_date,
        source_file,
        loaded_at
    from raw.telegram_messages

),

cleaned as (

    select
        md5(
            lower(trim(channel_name)) || '-' || cast(message_id as text)
        ) as message_key,

        cast(message_id as bigint) as message_id,

        lower(trim(channel_name)) as channel_name,

        cast(message_date as timestamp) as message_date,

        cast(message_date as date) as message_day,

        nullif(trim(message_text), '') as message_text,

        coalesce(cast(has_media as boolean), false) as has_media,

        image_path,

        coalesce(cast(views as integer), 0) as view_count,

        coalesce(cast(forwards as integer), 0) as forward_count,

        length(coalesce(message_text, '')) as message_length,

        case
            when image_path is not null then true
            else false
        end as has_image,

        cast(scrape_date as date) as scrape_date,

        source_file,

        cast(loaded_at as timestamp) as loaded_at

    from source

),

deduplicated as (

    select
        *,
        row_number() over (
            partition by message_key
            order by scrape_date desc nulls last, loaded_at desc nulls last
        ) as row_number_for_duplicate
    from cleaned
    where message_text is not null

),

final as (

    select
        message_key,
        message_id,
        channel_name,
        message_date,
        message_day,
        message_text,
        has_media,
        image_path,
        view_count,
        forward_count,
        message_length,
        has_image,
        scrape_date,
        source_file,
        loaded_at
    from deduplicated
    where row_number_for_duplicate = 1

)

select *
from final