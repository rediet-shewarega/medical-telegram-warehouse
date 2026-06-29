with messages as (

    select *
    from {{ ref('stg_telegram_messages') }}

),

channels as (

    select *
    from {{ ref('dim_channels') }}

),

dates as (

    select *
    from {{ ref('dim_dates') }}

),

final as (

    select
        m.message_key,
        m.message_id,

        c.channel_key,
        d.date_key,

        m.channel_name,
        m.message_date,
        m.message_day,
        m.scrape_date,

        m.message_text,
        m.message_length,

        m.view_count,
        m.forward_count,

        m.has_media,
        m.has_image,
        m.image_path,

        m.source_file,
        m.loaded_at

    from messages m

    left join channels c
        on m.channel_name = c.channel_name

    left join dates d
        on m.message_day = d.full_date

)

select *
from final