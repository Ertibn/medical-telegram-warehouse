-- Custom test: Ensure all messages have non-negative engagement metrics
-- Views and forwards should be >= 0 for all messages

select message_id
from {{ ref('fct_messages') }}
where views < 0 or forwards < 0
