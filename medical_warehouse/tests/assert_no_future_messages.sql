-- Custom test: Ensure no messages have future dates
-- This test fails if any message_date is in the future

select count(*) as future_messages
from {{ ref('fct_messages') }} f
join {{ ref('dim_dates') }} d on f.date_key = d.date_key
where d.full_date > current_date
having count(*) > 0
