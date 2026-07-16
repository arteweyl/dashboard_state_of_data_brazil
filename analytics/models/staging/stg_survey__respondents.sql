with respondents as (
    select
        2021 as survey_year,
        sha256('2021:' || p0_id) as respondent_key,
        try_cast(p1_a_idade as integer) as age,
        p1_a_a_faixa_idade as age_group,
        p1_b_genero as gender,
        cast(null as varchar) as race_ethnicity,
        cast(null as varchar) as disability,
        p1_e_a_uf_onde_mora as state_code,
        p1_e_b_regiao_onde_mora as region,
        p1_h_nivel_de_ensino as education_level,
        p1_i_area_de_formacao as education_area,
        p2_a_qual_sua_situacao_atual_de_trabalho as employment_status,
        p2_b_setor as industry,
        coalesce(p2_f_cargo_atual, p2_e_cargo_como_gestor) as role,
        p2_f_cargo_atual is null and p2_e_cargo_como_gestor is not null as role_was_harmonized,
        coalesce(p2_g_nivel, case when p2_e_cargo_como_gestor is not null then 'Gestão' end)
            as seniority,
        p2_h_faixa_salarial as salary_range,
        lower(p2_k_voce_esta_satisfeito_na_sua_empresa_atual) in ('1', 'true', 'sim')
            as is_satisfied,
        p2_q_atualmente_qual_a_sua_forma_de_trabalho as current_work_model,
        p2_r_qual_a_forma_de_trabalho_ideal_para_voce as ideal_work_model
    from {{ source('raw', 'survey_2021') }}

    union all

    select
        2022,
        sha256('2022:' || p0_id),
        try_cast(p1_a_idade as integer),
        p1_a_1_faixa_idade,
        p1_b_genero,
        p1_c_cor_raca_etnia,
        p1_d_pcd,
        p1_i_1_uf_onde_mora,
        p1_i_2_regiao_onde_mora,
        p1_l_nivel_de_ensino,
        p1_m_area_de_formacao,
        p2_a_qual_sua_situacao_atual_de_trabalho,
        p2_b_setor,
        coalesce(p2_f_cargo_atual, p2_e_cargo_como_gestor),
        p2_f_cargo_atual is null and p2_e_cargo_como_gestor is not null,
        coalesce(p2_g_nivel, case when p2_e_cargo_como_gestor is not null then 'Gestão' end),
        p2_h_faixa_salarial,
        lower(p2_k_voce_esta_satisfeito_na_sua_empresa_atual) in ('1', 'true', 'sim'),
        p2_p_atualmente_qual_a_sua_forma_de_trabalho,
        p2_q_qual_a_forma_de_trabalho_ideal_para_voce
    from {{ source('raw', 'survey_2022') }}

    union all

    select
        2023,
        sha256('2023:' || p0_id),
        try_cast(p1_a_idade as integer),
        p1_a_1_faixa_idade,
        p1_b_genero,
        p1_c_cor_raca_etnia,
        p1_d_pcd,
        p1_i_1_uf_onde_mora,
        p1_i_2_regiao_onde_mora,
        p1_l_nivel_de_ensino,
        p1_m_area_de_formacao,
        p2_a_qual_sua_situacao_atual_de_trabalho,
        p2_b_setor,
        coalesce(p2_f_cargo_atual, p2_e_cargo_como_gestor),
        p2_f_cargo_atual is null and p2_e_cargo_como_gestor is not null,
        coalesce(p2_g_nivel, case when p2_e_cargo_como_gestor is not null then 'Gestão' end),
        p2_h_faixa_salarial,
        lower(p2_k_voce_esta_satisfeito_na_sua_empresa_atual) in ('1', 'true', 'sim'),
        p2_r_atualmente_qual_a_sua_forma_de_trabalho,
        p2_s_qual_a_forma_de_trabalho_ideal_para_voce
    from {{ source('raw', 'survey_2023') }}

    union all

    select
        2024,
        sha256('2024:' || q_0_a_token),
        try_cast(q_1_a_idade as integer),
        q_1_a_1_faixa_idade,
        q_1_b_genero,
        q_1_c_cor_raca_etnia,
        q_1_d_pcd,
        q_1_i_1_uf_onde_mora,
        q_1_i_2_regiao_onde_mora,
        q_1_l_nivel_de_ensino,
        q_1_m_area_de_formacao,
        q_2_a_situacao_de_trabalho,
        q_2_b_setor,
        coalesce(q_2_f_cargo_atual, q_2_e_cargo_como_gestor),
        q_2_f_cargo_atual is null and q_2_e_cargo_como_gestor is not null,
        coalesce(q_2_g_nivel, case when q_2_e_cargo_como_gestor is not null then 'Gestão' end),
        q_2_h_faixa_salarial,
        lower(q_2_k_satisfeito_atualmente) in ('1', 'true', 'sim'),
        q_2_r_modelo_de_trabalho_atual,
        q_2_s_modelo_de_trabalho_ideal
    from {{ source('raw', 'survey_2024') }}

    union all

    select
        2025,
        sha256('2025:' || q_0_a_token),
        try_cast(q_1_a_idade as integer),
        q_1_a_1_faixa_idade,
        q_1_b_genero,
        q_1_c_cor_raca_etnia,
        q_1_d_pcd,
        q_1_i_1_uf_onde_mora,
        q_1_i_2_regiao_onde_mora,
        q_1_l_nivel_de_ensino,
        q_1_m_area_de_formacao,
        q_2_a_situacao_de_trabalho,
        q_2_b_setor,
        coalesce(q_2_f_cargo_atual, q_2_e_cargo_como_gestor),
        q_2_f_cargo_atual is null and q_2_e_cargo_como_gestor is not null,
        coalesce(q_2_g_nivel, case when q_2_e_cargo_como_gestor is not null then 'Gestão' end),
        q_2_h_faixa_salarial,
        lower(q_2_k_satisfeito_atualmente) in ('1', 'true', 'sim'),
        q_2_q_modelo_de_trabalho_atual,
        q_2_r_modelo_de_trabalho_ideal
    from {{ source('raw', 'survey_2025') }}
),

validated as (
    select
        *,
        employment_status is not null
        and lower(employment_status) not like 'desempregado%'
        and lower(employment_status) not like 'somente estudante%'
        and lower(employment_status) != 'prefiro não informar' as is_currently_working
    from respondents
    where age is null or age between 16 and 100
)

select *
from validated
qualify row_number() over (partition by respondent_key order by survey_year) = 1
