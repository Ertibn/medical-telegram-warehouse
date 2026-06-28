-- Dimension table: Channels
-- Contains metadata about Telegram channels

with channels as (
    select distinct
        channel_name,
        channel_username
    from {{ ref('stg_telegram_messages') }}
    where channel_name is not null
),

enriched as (
    select
        {{ dbt_utils.generate_surrogate_key(['channel_username']) }} as channel_key,
        channel_name,
        channel_username,
        -- Classify channel type based on name
        case
            when channel_name like '%Pharma%' or channel_name like '%Pharmacy%' then 'Pharmaceutical'
            when channel_name like '%Cosmetic%' or channel_name like '%Skincare%' then 'Cosmetics'
            else 'Medical'
        end as channel_type,
        current_timestamp as created_at
    from channels
)

select * from enriched
