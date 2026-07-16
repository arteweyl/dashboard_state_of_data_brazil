-- The contracted raw files contain 20,921 rows and 8 exact duplicate responses.
select count(*) as actual_rows
from {{ ref('stg_survey__respondents') }}
having count(*) != 20913

