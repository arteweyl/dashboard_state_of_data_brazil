with questions as (
    select
        survey_year,
        respondent_key,
        'age' as question_key,
        'Idade' as question_label,
        true as is_available,
        true as is_eligible,
        cast(age as varchar) as answer
    from {{ ref('stg_survey__respondents') }}
    union all
    select survey_year, respondent_key, 'age_group', 'Faixa etária', true, true, age_group
    from {{ ref('stg_survey__respondents') }}
    union all
    select survey_year, respondent_key, 'gender', 'Gênero', true, true, gender
    from {{ ref('stg_survey__respondents') }}
    union all
    select
        survey_year,
        respondent_key,
        'race_ethnicity',
        'Cor, raça ou etnia',
        survey_year >= 2022,
        survey_year >= 2022,
        race_ethnicity
    from {{ ref('stg_survey__respondents') }}
    union all
    select
        survey_year,
        respondent_key,
        'disability',
        'Pessoa com deficiência',
        survey_year >= 2022,
        survey_year >= 2022,
        disability
    from {{ ref('stg_survey__respondents') }}
    union all
    select survey_year, respondent_key, 'region', 'Região', true, true, region
    from {{ ref('stg_survey__respondents') }}
    union all
    select
        survey_year,
        respondent_key,
        'education_level',
        'Escolaridade',
        true,
        true,
        education_level
    from {{ ref('stg_survey__respondents') }}
    union all
    select
        survey_year,
        respondent_key,
        'education_area',
        'Área de formação',
        true,
        true,
        education_area
    from {{ ref('stg_survey__respondents') }}
    union all
    select
        survey_year,
        respondent_key,
        'employment_status',
        'Situação profissional',
        true,
        true,
        employment_status
    from {{ ref('stg_survey__respondents') }}
    union all
    select
        survey_year, respondent_key, 'industry', 'Setor', true, is_currently_working, industry
    from {{ ref('stg_survey__respondents') }}
    union all
    select survey_year, respondent_key, 'role', 'Cargo', true, is_currently_working, role
    from {{ ref('stg_survey__respondents') }}
    union all
    select
        survey_year,
        respondent_key,
        'seniority',
        'Senioridade',
        true,
        is_currently_working,
        seniority
    from {{ ref('stg_survey__respondents') }}
    union all
    select
        survey_year,
        respondent_key,
        'salary_range',
        'Faixa salarial',
        true,
        is_currently_working,
        salary_range
    from {{ ref('stg_survey__respondents') }}
    union all
    select
        survey_year,
        respondent_key,
        'is_satisfied',
        'Satisfação profissional',
        true,
        is_currently_working,
        cast(is_satisfied as varchar)
    from {{ ref('stg_survey__respondents') }}
    union all
    select
        survey_year,
        respondent_key,
        'current_work_model',
        'Modelo de trabalho atual',
        true,
        is_currently_working,
        current_work_model
    from {{ ref('stg_survey__respondents') }}
    union all
    select
        survey_year,
        respondent_key,
        'ideal_work_model',
        'Modelo de trabalho ideal',
        true,
        is_currently_working,
        ideal_work_model
    from {{ ref('stg_survey__respondents') }}
),

summarized as (
    select
        survey_year,
        question_key,
        question_label,
        case when bool_or(is_available) then 'Disponível' else 'Não perguntado' end
            as question_status,
        count(distinct respondent_key) as total_respondents,
        count(distinct case when is_available and is_eligible then respondent_key end)
            as eligible_respondents,
        count(
            distinct case
                when is_available and is_eligible and nullif(trim(answer), '') is not null
                    then respondent_key
            end
        ) as answered_respondents
    from questions
    group by all
)

select
    *,
    eligible_respondents - answered_respondents as missing_respondents,
    case
        when question_status = 'Disponível'
            then total_respondents - eligible_respondents
        else 0
    end as not_applicable_respondents,
    round(100.0 * answered_respondents / nullif(eligible_respondents, 0), 1) as coverage_pct
from summarized

