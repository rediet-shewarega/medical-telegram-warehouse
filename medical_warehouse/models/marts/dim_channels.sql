with messages as (

    select *
    from {{ ref('stg_telegram_messages') }}

),

channel_summary as (

    select
        row_number() over (order by channel_name) as channel_key,

        channel_name,

        case
            when channel_name like '%pharma%' then 'Pharmaceutical'
            when channel_name like '%tikvah%' then 'Pharmaceutical'

            when channel_name like '%cosmetic%' then 'Cosmetics'
            when channel_name like '%lobelia%' then 'Cosmetics'

            when channel_name like '%chemed%' then 'Medical'
            when channel_name like '%hakim%' then 'Medical'
            when channel_name like '%guideline%' then 'Medical'
            when channel_name like '%medical%' then 'Medical'

            else 'Medical'
        end as channel_type,

        min(message_day) as first_post_date,
        max(message_day) as last_post_date,
        count(*) as total_posts,
        round(avg(view_count), 2) as avg_views

    from messages
    group by channel_name

)

select *
from channel_summary