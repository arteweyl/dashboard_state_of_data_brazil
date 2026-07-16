select
    survey_year,
    coalesce(region, 'Não informado') as region,
    coalesce(gender, 'Não informado') as gender,
    coalesce(seniority, 'Não informado') as seniority,
    coalesce(current_work_model, 'Não informado') as current_work_model,
    count(*) as respondents,
    round(avg(age), 1) as average_age,
    round(
        100.0 * avg(case when is_satisfied then 1 when is_satisfied = false then 0 end),
        1
    ) as satisfied_pct
from {{ ref('stg_survey__respondents') }}
group by all
having count(*) >= 10
