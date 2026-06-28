-- Fact table: Messages
-- Central fact table for message analytics

with stg_messages as (
    select * from {{ ref('stg_telegram_messages') }}
),

dim_channels as (
    select * from {{ ref('dim_channels') }}
),

dim_dates as (
    select * from {{ ref('dim_dates') }}
),

joined as (
    select
        msg.message_id,
        dc.channel_key,
        dd.date_key,
        msg.message_text,
        msg.message_length,
        msg.views,
        msg.forwards,
        msg.has_media,
        msg.has_image_flag,
        msg.media_type,
        msg.loaded_at
    from stg_messages msg
    left join dim_channels dc
        on msg.channel_username = dc.channel_username
    left join dim_dates dd
        on cast(msg.message_date as date) = dd.date_key
)

select * from joined
