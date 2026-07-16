with cloud_flags as (
    select
        2021 as survey_year,
        sha256('2021:' || p0_id) as respondent_key,
        'Uso no trabalho' as question_context,
        p4_g_a_amazon_web_services_aws as aws,
        p4_g_b_google_cloud_gcp as gcp,
        p4_g_c_azure_microsoft as azure,
        p4_g_d_oracle_cloud as oracle_cloud,
        p4_g_e_ibm as ibm,
        p4_g_f_servidores_on_premise_nao_utilizamos_cloud as on_premise,
        p4_g_g_cloud_propria as private_cloud
    from {{ source('raw', 'survey_2021') }}

    union all

    select
        2022,
        sha256('2022:' || p0_id),
        'Cloud preferida',
        p4_h_2_amazon_web_services_aws,
        p4_h_3_google_cloud_gcp,
        p4_h_1_azure_microsoft,
        cast(null as varchar),
        cast(null as varchar),
        cast(null as varchar),
        cast(null as varchar)
    from {{ source('raw', 'survey_2022') }}

    union all

    select
        2023,
        sha256('2023:' || p0_id),
        'Cloud preferida',
        p4_h_2_amazon_web_services_aws,
        p4_h_3_google_cloud_gcp,
        p4_h_1_azure_microsoft,
        p4_h_4_oracle_cloud,
        p4_h_5_ibm,
        p4_h_6_servidores_on_premise_nao_utilizamos_cloud,
        p4_h_7_cloud_propria
    from {{ source('raw', 'survey_2023') }}

    union all

    select
        2024,
        sha256('2024:' || q_0_a_token),
        'Uso no dia a dia',
        q_4_h_1_amazon_web_services_aws,
        q_4_h_2_google_cloud_gcp,
        q_4_h_3_azure_microsoft,
        q_4_h_4_oracle_cloud,
        q_4_h_5_ibm,
        q_4_h_6_servidores_on_premise_nao_utilizamos_cloud,
        q_4_h_7_cloud_propria
    from {{ source('raw', 'survey_2024') }}

    union all

    select
        2025,
        sha256('2025:' || q_0_a_token),
        'Uso no dia a dia',
        q_4_e_1_amazon_web_services_aws,
        q_4_e_2_google_cloud_gcp,
        q_4_e_3_azure_microsoft,
        q_4_e_4_oracle_cloud,
        q_4_e_5_ibm,
        q_4_e_6_servidores_on_premise_nao_utilizamos_cloud,
        q_4_e_7_cloud_propria
    from {{ source('raw', 'survey_2025') }}
),

deduplicated as (
    select *
    from cloud_flags
    qualify row_number() over (partition by respondent_key order by survey_year) = 1
),

cloud_mentions as (
    unpivot deduplicated
    on aws, gcp, azure, oracle_cloud, ibm, on_premise, private_cloud
    into name cloud value selected
)

select
    survey_year,
    question_context,
    cloud,
    count(distinct respondent_key) as respondents
from cloud_mentions
where selected = '1'
group by all
having count(distinct respondent_key) >= 10

