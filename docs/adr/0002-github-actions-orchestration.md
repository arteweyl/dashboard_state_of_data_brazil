# ADR 0002: GitHub Actions como orquestrador

## Status

Aceito.

## Contexto

O projeto precisa sincronizar fontes anuais do Kaggle, carregar o DuckDB, executar transformações
dbt, validar os produtos públicos e publicar um site estático. `uv` gerencia ambiente e lockfile,
mas não oferece agenda, dependências operacionais, histórico de execuções ou controle de deploy.

Uma instalação permanente de Airflow adicionaria scheduler, banco de metadados e operação de
workers para uma carga pequena, anual e mantida no GitHub.

## Decisão

Usar GitHub Actions para orquestração e GitHub Pages para servir o artefato. A pipeline possui três
fronteiras executáveis e independentes:

1. `scripts/ingest.sh`: sincroniza fontes contratadas e carrega o warehouse;
2. `scripts/transform.sh`: resolve pacotes e executa `dbt build`;
3. `scripts/build_site.sh`: gera e valida o HTML, snapshot e DuckDB público.

O runner instala o ambiente uma vez com `uv sync --all-groups --locked`. Depois disso, os scripts
chamam diretamente os executáveis da `.venv`. O token do Kaggle entra pelo secret
`KAGGLE_API_TOKEN`; no desenvolvimento local, pode vir do `.env` ignorado pelo Git.

O workflow roda manualmente, em mudanças relevantes da branch `main` e mensalmente para verificar
as fontes. O deploy depende do job de build e recebe permissões mínimas próprias para Pages.

## Consequências

- cada etapa pode ser reproduzida localmente sem simular o GitHub Actions;
- falhas de fonte, contrato, dbt ou publicação impedem o deploy;
- logs e histórico ficam associados a cada execução do workflow;
- `site/` e o warehouse são artefatos reconstruíveis, não código versionado;
- uma migração futura para Airflow continua possível porque as operações não dependem do runner.
