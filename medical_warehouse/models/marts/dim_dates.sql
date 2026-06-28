-- Dimension table: Dates
-- Standard date dimension for time-based analysis

{% set start_date = '2024-01-01' %}
{% set end_date = '2026-12-31' %}

with date_spine as (
    {% if execute %}
        {%- set date_list = range(
            start_date | strptime('%Y-%m-%d') | int,
            end_date | strptime('%Y-%m-%d') | int,
            86400
        ) -%}
        
        select
            to_date(to_timestamp(date_value), 'YYYY-MM-DD') as date_value
        from (
            {% set dates = [] %}
            {% for date_int in date_list %}
                {% set dates = dates.append(
                    to_timestamp(date_int) | strftime('%Y-%m-%d')
                ) %}
            {% endfor %}
            select generate_series(
                '{{ start_date }}'::date,
                '{{ end_date }}'::date,
                interval '1 day'
            ) as date_value
        ) t
    {% else %}
        select generate_series(
            '{{ start_date }}'::date,
            '{{ end_date }}'::date,
            interval '1 day'
        ) as date_value
    {% endif %}
),

with_calcs as (
    select
        date_value as date_key,
        date_value as full_date,
        extract(dow from date_value) as day_of_week,
        to_char(date_value, 'Day') as day_name,
        extract(week from date_value) as week_of_year,
        extract(month from date_value) as month,
        to_char(date_value, 'Month') as month_name,
        extract(quarter from date_value) as quarter,
        extract(year from date_value) as year,
        case
            when extract(dow from date_value) in (0, 6) then true
            else false
        end as is_weekend
    from date_spine
)

select * from with_calcs
