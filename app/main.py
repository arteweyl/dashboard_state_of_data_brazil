"""Interactive public dashboard backed only by privacy-safe dbt marts."""

from __future__ import annotations

import os
from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

DEFAULT_DATABASE = Path("data/warehouse/state_of_data.duckdb")
DATABASE = Path(os.getenv("STATE_OF_DATA_DB_PATH", DEFAULT_DATABASE.as_posix()))
MART_SCHEMA = "analytics_marts"
ALLOWED_MARTS = {
    "annual_summary",
    "categorical_distribution",
    "data_quality",
    "technology_cloud",
}
COLORS = ["#8B5CF6", "#22D3EE", "#F472B6", "#FBBF24", "#34D399"]
CLOUD_LABELS = {
    "aws": "AWS",
    "gcp": "Google Cloud",
    "azure": "Microsoft Azure",
    "oracle_cloud": "Oracle Cloud",
    "ibm": "IBM Cloud",
    "on_premise": "On-premise",
    "private_cloud": "Cloud própria",
}


@st.cache_data(show_spinner=False)
def load_mart(table: str) -> pd.DataFrame:
    """Read one allow-listed aggregate mart without exposing row-level data."""

    if table not in ALLOWED_MARTS:
        raise ValueError("Mart não autorizado.")
    with duckdb.connect(DATABASE.as_posix(), read_only=True) as connection:
        return connection.execute(f"SELECT * FROM {MART_SCHEMA}.{table}").df()


def distribution_figure(
    distributions: pd.DataFrame,
    dimension: str,
    year: int,
    title: str,
    top_n: int = 10,
):  # type: ignore[no-untyped-def]
    """Build a compact horizontal ranking for one privacy-safe dimension."""

    frame = distributions[
        (distributions["dimension"] == dimension) & (distributions["survey_year"] == year)
    ].copy()
    frame = frame.nlargest(top_n, "respondents").sort_values("respondents")
    figure = px.bar(
        frame,
        x="respondents",
        y="category",
        orientation="h",
        title=title,
        text_auto=True,
        color="respondents",
        color_continuous_scale=[COLORS[0], COLORS[1]],
        labels={"category": "", "respondents": "Respondentes"},
    )
    figure.update_layout(
        coloraxis_showscale=False,
        height=390,
        margin={"l": 10, "r": 10, "t": 55, "b": 20},
    )
    return figure


def render_pair(
    distributions: pd.DataFrame,
    quality: pd.DataFrame,
    year: int,
    left_config: tuple[str, str, int],
    right_config: tuple[str, str, int],
) -> None:
    """Render two related distributions side by side."""

    left, right = st.columns(2)
    left.plotly_chart(
        distribution_figure(distributions, left_config[0], year, left_config[1], left_config[2]),
        width="stretch",
    )
    left.caption(coverage_text(quality, left_config[0], year))
    right.plotly_chart(
        distribution_figure(distributions, right_config[0], year, right_config[1], right_config[2]),
        width="stretch",
    )
    right.caption(coverage_text(quality, right_config[0], year))


def coverage_text(quality: pd.DataFrame, question_key: str, year: int) -> str:
    """Explain the denominator and missingness for a displayed question."""

    row = quality[(quality["question_key"] == question_key) & (quality["survey_year"] == year)]
    if row.empty:
        return "Cobertura não calculada para esta pergunta."
    metric = row.iloc[0]
    if metric["question_status"] == "Não perguntado":
        return "Esta pergunta não fazia parte dessa edição."
    return (
        f"Base: {int(metric['answered_respondents']):,} respostas de "
        f"{int(metric['eligible_respondents']):,} participantes elegíveis "
        f"({metric['coverage_pct']:.1f}% de cobertura)."
    ).replace(",", ".")


st.set_page_config(
    page_title="State of Data Brasil",
    page_icon="🪐",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("State of Data Brasil")
st.caption("Uma órbita pelos dados, carreiras e transformações do ecossistema brasileiro.")

if not DATABASE.is_file():
    st.error("Warehouse ainda não construído. Execute `make ingest` e `make transform`.")
    st.stop()

try:
    annual = load_mart("annual_summary")
    distributions = load_mart("categorical_distribution")
    quality = load_mart("data_quality")
    cloud = load_mart("technology_cloud")
except duckdb.Error as error:
    st.error(f"Não foi possível ler os marts. Reconstrua o pipeline. Detalhe: {error}")
    st.stop()

available_years = sorted(int(year) for year in annual["survey_year"].unique())
selected_years = st.sidebar.multiselect(
    "Edições na série histórica",
    options=available_years,
    default=available_years,
)
if not selected_years:
    st.warning("Selecione ao menos uma edição.")
    st.stop()

highlight_year = st.sidebar.selectbox(
    "Edição em destaque",
    options=sorted(selected_years, reverse=True),
)
st.sidebar.caption("Os rankings das abas usam a edição em destaque.")

filtered_annual = annual[annual["survey_year"].isin(selected_years)].sort_values("survey_year")
latest = annual[annual["survey_year"] == highlight_year].iloc[0]

tabs = st.tabs(
    [
        "🪐 Visão geral",
        "👥 Perfil",
        "🚀 Carreira",
        "🏠 Trabalho",
        "🛠️ Tecnologias",
        "✅ Qualidade dos dados",
        "📖 Metodologia",
    ]
)

with tabs[0]:
    kpi_1, kpi_2, kpi_3 = st.columns(3)
    kpi_1.metric(
        f"Respostas em {highlight_year}",
        f"{int(latest['respondents']):,}".replace(",", "."),
    )
    kpi_2.metric(f"Idade média em {highlight_year}", f"{latest['average_age']:.1f}")
    kpi_3.metric(f"Satisfação em {highlight_year}", f"{latest['satisfied_pct']:.1f}%")

    participation = px.line(
        filtered_annual,
        x="survey_year",
        y="respondents",
        markers=True,
        title="Participação por edição",
        color_discrete_sequence=COLORS,
        labels={"survey_year": "Ano", "respondents": "Respondentes"},
    )
    participation.update_layout(xaxis_dtick=1, height=390)

    satisfaction = px.line(
        filtered_annual,
        x="survey_year",
        y="satisfied_pct",
        markers=True,
        title="Satisfação profissional",
        color_discrete_sequence=[COLORS[2]],
        labels={"survey_year": "Ano", "satisfied_pct": "Satisfação (%)"},
    )
    satisfaction.update_layout(xaxis_dtick=1, yaxis_ticksuffix="%", height=390)

    left, right = st.columns(2)
    left.plotly_chart(participation, width="stretch")
    right.plotly_chart(satisfaction, width="stretch")
    st.plotly_chart(
        distribution_figure(distributions, "region", highlight_year, "Distribuição regional", 8),
        width="stretch",
    )
    st.caption(coverage_text(quality, "region", highlight_year))

with tabs[1]:
    st.subheader(f"Quem respondeu à edição de {highlight_year}")
    render_pair(
        distributions,
        quality,
        highlight_year,
        ("age_group", "Faixa etária", 10),
        ("gender", "Gênero", 10),
    )
    render_pair(
        distributions,
        quality,
        highlight_year,
        ("race_ethnicity", "Cor, raça ou etnia", 10),
        ("education_level", "Escolaridade", 10),
    )
    render_pair(
        distributions,
        quality,
        highlight_year,
        ("region", "Região", 8),
        ("education_area", "Áreas de formação — top 10", 10),
    )

with tabs[2]:
    st.subheader(f"Carreira e mercado em {highlight_year}")
    render_pair(
        distributions,
        quality,
        highlight_year,
        ("role", "Cargos — top 12", 12),
        ("seniority", "Senioridade", 10),
    )
    render_pair(
        distributions,
        quality,
        highlight_year,
        ("salary_range", "Faixa salarial", 14),
        ("industry", "Setores — top 12", 12),
    )

with tabs[3]:
    st.subheader(f"Relações e modelos de trabalho em {highlight_year}")
    render_pair(
        distributions,
        quality,
        highlight_year,
        ("employment_status", "Situação profissional", 12),
        ("current_work_model", "Modelo de trabalho atual", 10),
    )
    st.plotly_chart(
        distribution_figure(
            distributions,
            "ideal_work_model",
            highlight_year,
            "Modelo de trabalho ideal",
            10,
        ),
        width="stretch",
    )
    st.caption(coverage_text(quality, "ideal_work_model", highlight_year))

with tabs[4]:
    st.subheader("Ecossistema de cloud")
    st.warning(
        "A formulação mudou entre edições: 2021 mede uso no trabalho; 2022-2023, preferência; "
        "2024-2025, uso no dia a dia. Compare tendências considerando esse contexto."
    )
    cloud_filtered = cloud[cloud["survey_year"].isin(selected_years)].copy()
    cloud_filtered["cloud_label"] = cloud_filtered["cloud"].map(CLOUD_LABELS)
    cloud_highlight = cloud_filtered[cloud_filtered["survey_year"] == highlight_year]

    cloud_bar = px.bar(
        cloud_highlight.sort_values("respondents"),
        x="respondents",
        y="cloud_label",
        orientation="h",
        text_auto=True,
        title=f"Clouds citadas em {highlight_year}",
        color="respondents",
        color_continuous_scale=[COLORS[0], COLORS[1]],
        labels={"cloud_label": "", "respondents": "Respondentes"},
    )
    cloud_bar.update_layout(coloraxis_showscale=False, height=410)

    major_clouds = cloud_filtered[cloud_filtered["cloud"].isin(["aws", "gcp", "azure"])]
    cloud_trend = px.line(
        major_clouds,
        x="survey_year",
        y="respondents",
        color="cloud_label",
        markers=True,
        title="AWS, Google Cloud e Azure por edição",
        color_discrete_sequence=COLORS,
        labels={"survey_year": "Ano", "respondents": "Menções", "cloud_label": "Cloud"},
    )
    cloud_trend.update_layout(xaxis_dtick=1, height=410)

    left, right = st.columns(2)
    left.plotly_chart(cloud_bar, width="stretch")
    right.plotly_chart(cloud_trend, width="stretch")

with tabs[5]:
    st.subheader(f"Cobertura das perguntas em {highlight_year}")
    st.markdown(
        "Cobertura é a proporção de participantes elegíveis que forneceram uma resposta válida. "
        "Pessoas para quem a pergunta não se aplicava não entram no denominador."
    )
    quality_year = quality[quality["survey_year"] == highlight_year].copy()
    available_quality = quality_year[quality_year["question_status"] == "Disponível"].copy()

    quality_chart = px.bar(
        available_quality.sort_values("coverage_pct"),
        x="coverage_pct",
        y="question_label",
        orientation="h",
        text="coverage_pct",
        title="Cobertura por pergunta",
        color="coverage_pct",
        color_continuous_scale=["#F472B6", "#FBBF24", "#34D399"],
        range_color=[0, 100],
        labels={"coverage_pct": "Cobertura (%)", "question_label": ""},
    )
    quality_chart.update_traces(texttemplate="%{text:.1f}%")
    quality_chart.update_layout(coloraxis_showscale=False, xaxis_range=[0, 100], height=600)
    st.plotly_chart(quality_chart, width="stretch")

    quality_table = quality_year[
        [
            "question_label",
            "question_status",
            "eligible_respondents",
            "answered_respondents",
            "missing_respondents",
            "not_applicable_respondents",
            "coverage_pct",
        ]
    ].rename(
        columns={
            "question_label": "Pergunta",
            "question_status": "Situação",
            "eligible_respondents": "Elegíveis",
            "answered_respondents": "Responderam",
            "missing_respondents": "Sem resposta",
            "not_applicable_respondents": "Não aplicável",
            "coverage_pct": "Cobertura (%)",
        }
    )
    st.dataframe(quality_table, hide_index=True, width="stretch")
    st.caption(
        "“Não perguntado” significa que a pergunta não existia naquela edição. “Não aplicável” "
        "indica participantes que, pelo fluxo do questionário, não precisavam responder."
    )

with tabs[6]:
    st.subheader("Sobre os dados e os resultados")
    st.markdown(
        """
        Este painel reúne respostas das pesquisas **State of Data Brasil de 2021 a 2025**. Como os
        questionários mudaram ao longo do tempo, perguntas equivalentes foram organizadas com os
        mesmos nomes para permitir a comparação entre as edições. Quando uma pergunta não existia
        em determinado ano, o painel mantém essa informação como ausente em vez de estimar uma
        resposta.
        """
    )

    methodology_left, methodology_right = st.columns(2)
    with methodology_left:
        st.markdown(
            """
            #### Como os dados foram preparados

            - Os arquivos foram conferidos para garantir que não sofreram alterações inesperadas.
            - Foram encontradas oito respostas repetidas de forma idêntica; cada repetição foi
              contada apenas uma vez.
            - Respostas em branco não são tratadas como “não”, “insatisfeito” ou zero.
            - Quando outra resposta permite completar um campo sem ambiguidade, aplicamos uma
              regra lógica. Exemplo: o cargo informado no campo de gestão completa o cargo geral.
            - O percentual de satisfação considera somente quem respondeu a essa pergunta.
            - Quando a redação de uma pergunta mudou, o painel apresenta um aviso próximo ao
              gráfico correspondente.
            """
        )
    with methodology_right:
        st.markdown(
            """
            #### Como protegemos os participantes

            - O painel mostra somente resultados de grupos, nunca respostas de uma pessoa.
            - Nomes, códigos de identificação e tokens não são exibidos.
            - Categorias com menos de 10 respostas são ocultadas para dificultar a identificação
              de participantes.
            - Os arquivos com as respostas completas não são publicados junto com o código do
              painel.
            """
        )

    st.markdown(
        """
        #### Como interpretar os números

        A pesquisa foi respondida voluntariamente por pessoas da comunidade de dados. Por isso, os
        resultados descrevem **quem participou da pesquisa**, mas não representam necessariamente
        todas as pessoas que trabalham com dados no Brasil. Diferenças entre anos podem refletir
        tanto mudanças no mercado quanto mudanças no perfil dos participantes ou nas perguntas.

        Os totais de gráficos detalhados podem ser menores que o total geral da edição. Isso ocorre
        quando uma pessoa não respondeu àquela pergunta ou quando uma categoria com menos de 10
        respostas foi ocultada para proteger os participantes.

        O painel não usa preenchimento estatístico para adivinhar respostas. Esse tipo de técnica
        exige um modelo validado, pesos amostrais e indicadores que permitam distinguir valores
        observados de estimados. Como esses elementos não acompanham todas as edições, a opção mais
        transparente é medir e publicar a cobertura de cada pergunta.
        """
    )

    st.caption(
        "Fonte: pesquisas State of Data Brasil, disponibilizadas no Kaggle. O painel preserva as "
        "licenças e a atribuição indicadas nas páginas de cada edição."
    )

st.caption(
    "Proteção dos participantes: o painel apresenta somente resultados agrupados. Nenhum "
    "identificador ou resposta individual é exibido, e grupos com menos de 10 respostas são "
    "ocultados."
)
