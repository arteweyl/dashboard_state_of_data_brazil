# ADR 0001: stack analítica open source e local-first

- Status: aceito
- Data: 2026-07-16

## Contexto

O produto começa com cinco CSVs, cerca de 21 mil respostas e schemas heterogêneos. Precisa ser
reproduzível no WSL2, barato para desenvolver, simples de revisar e apto a crescer sem operar uma
plataforma distribuída prematuramente.

## Decisão

Adotar uv, Python, DuckDB, dbt Core com dbt-duckdb e Streamlit/Plotly. Separar fontes brutas,
staging harmonizado e marts agregados. Usar GitHub Actions para lint, tipos, testes, parse do dbt e
auditoria de dependências.

## Consequências

- Desenvolvimento e CI não dependem de um warehouse remoto.
- SQL, linhagem, contratos e testes ficam próximos do código.
- O arquivo DuckDB é reconstruível e não entra no Git.
- Concorrência alta, autenticação multiusuário e atualização contínua não são objetivos desta fase.
- Se volume, SLA ou colaboração exigirem outro warehouse, os modelos dbt e contratos reduzem o
  custo da migração, que deverá ganhar um novo ADR.

## Alternativas consideradas

Superset e Airflow oferecem mais recursos operacionais, mas adicionariam serviços e manutenção sem
resolver uma necessidade atual. Transformações apenas em notebooks prejudicariam testes,
rastreabilidade e revisão. Uma nuvem proprietária contraria o requisito open source e aumentaria
custo e acoplamento nesta etapa.

