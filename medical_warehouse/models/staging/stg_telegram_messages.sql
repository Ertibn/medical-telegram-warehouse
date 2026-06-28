-- Staging model: Clean and standardize raw telegram messages
-- Remove duplicates, cast data types, add calculated fields

with source as (
    select
        message_id,
        channel_name,
        channel_username,
        message_date,
        message_text,
        has_media,
        image_path,
        views,
        forwards,
        media_type,
        loaded_at
    from raw.telegram_messages
),

cleaned as (
    select
        message_id,
        channel_name,
        channel_username,
        -- Cast date to proper timestamp
        case 
            when message_date is not null then message_date::timestamp
            else null 
        end as message_date,
        -- Trim and clean text
        trim(message_text) as message_text,
        -- Ensure boolean
        coalesce(has_media, false) as has_media,
        -- Path to image
        image_path,
        -- Ensure non-negative views
        greatest(coalesce(views, 0), 0) as views,
        -- Ensure non-negative forwards
        greatest(coalesce(forwards, 0), 0) as forwards,
        -- Media type
        media_type,
        -- Loading timestamp
        loaded_at::timestamp as loaded_at
    from source
    where
        -- Remove empty messages
        trim(message_text) != ''
        and message_id is not null
),

with_calcs as (
    select
        message_id,
        channel_name,
        channel_username,
        message_date,
        message_text,
        has_media,
        image_path,
        views,
        forwards,
        media_type,
        loaded_at,
        -- Calculated fields
        length(message_text) as message_length,
        case when image_path is not null then true else false end as has_image_flag,
        row_number() over (partition by message_id, channel_username order by loaded_at desc) as rn
    from cleaned
)

select
    message_id,
    channel_name,
    channel_username,
    message_date,
    message_text,
    has_media,
    image_path,
    views,
    forwards,
    media_type,
    loaded_at,
    message_length,
    has_image_flag
from with_calcs
where rn = 1  -- Remove duplicates, keeping latest
