-- Fact table: Image Detections
-- Integrates YOLO object detection results with message facts

with yolo_results as (
    select
        message_id::integer,
        channel_name,
        detected_class,
        confidence_score,
        image_category,
        num_objects
    from raw.image_detections
    where message_id is not null
),

fct_messages as (
    select * from {{ ref('fct_messages') }}
),

dim_channels as (
    select * from {{ ref('dim_channels') }}
),

joined as (
    select
        yr.message_id,
        dc.channel_key,
        fm.date_key,
        yr.detected_class,
        yr.confidence_score,
        yr.image_category,
        yr.num_objects,
        fm.views,
        fm.forwards,
        fm.has_media
    from yolo_results yr
    left join dim_channels dc
        on yr.channel_name = dc.channel_name
    left join fct_messages fm
        on yr.message_id = fm.message_id
    where yr.message_id is not null
)

select * from joined
