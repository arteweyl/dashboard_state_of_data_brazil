select
    survey_year,
    count(*) as respondents,
    round(avg(age), 1) as average_age,
    round(
        100.0 * avg(case when is_satisfied then 1 when is_satisfied = false then 0 end),
        1
    ) as satisfied_pct
from {{ ref('stg_survey__respondents') }}
group by survey_year
