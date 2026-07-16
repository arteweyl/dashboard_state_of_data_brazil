with dimensions as (
    select survey_year, respondent_key, 'region' as dimension, region as category
    from {{ ref('stg_survey__respondents') }}
    union all
    select survey_year, respondent_key, 'gender', gender
    from {{ ref('stg_survey__respondents') }}
    union all
    select survey_year, respondent_key, 'race_ethnicity', race_ethnicity
    from {{ ref('stg_survey__respondents') }}
    union all
    select survey_year, respondent_key, 'age_group', age_group
    from {{ ref('stg_survey__respondents') }}
    union all
    select survey_year, respondent_key, 'education_level', education_level
    from {{ ref('stg_survey__respondents') }}
    union all
    select survey_year, respondent_key, 'education_area', education_area
    from {{ ref('stg_survey__respondents') }}
    union all
    select survey_year, respondent_key, 'employment_status', employment_status
    from {{ ref('stg_survey__respondents') }}
    union all
    select survey_year, respondent_key, 'industry', industry
    from {{ ref('stg_survey__respondents') }}
    union all
    select survey_year, respondent_key, 'role', role
    from {{ ref('stg_survey__respondents') }}
    union all
    select survey_year, respondent_key, 'seniority', seniority
    from {{ ref('stg_survey__respondents') }}
    union all
    select survey_year, respondent_key, 'salary_range', salary_range
    from {{ ref('stg_survey__respondents') }}
    union all
    select survey_year, respondent_key, 'current_work_model', current_work_model
    from {{ ref('stg_survey__respondents') }}
    union all
    select survey_year, respondent_key, 'ideal_work_model', ideal_work_model
    from {{ ref('stg_survey__respondents') }}
)

select
    survey_year,
    dimension,
    trim(category) as category,
    count(distinct respondent_key) as respondents
from dimensions
where category is not null and trim(category) != ''
group by all
having count(distinct respondent_key) >= 10

