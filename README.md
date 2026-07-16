# State of Data Brasil

Dashboard open source para investigar a evolução do mercado brasileiro de dados entre as edições
2021 e 2025 do State of Data, com rastreabilidade, testes de qualidade e privacidade por design.

## Objetivo da primeira entrega

Construir uma fundação reproduzível que:

- valide fontes imutáveis antes da ingestão;
- harmonize mudanças de schema entre as edições sem apagar diferenças históricas;
- nunca exponha tokens ou respostas individuais no dashboard;
- produza indicadores anuais e segmentos com limiar mínimo de 10 respostas;
- possa ser verificada localmente e em CI com os mesmos comandos.

O dashboard inicial responde três perguntas: como a participação evoluiu, como ela se distribui por
região e como variou a satisfação profissional. Novas perguntas entram como incrementos pequenos,
com contrato e teste próprios.

## Stack

| Camada | Tecnologia | Papel |
| --- | --- | --- |
| Ambiente | uv | Python e lockfile reproduzíveis |
| Warehouse | DuckDB | OLAP local, portátil e sem servidor |
| Transformação | dbt Core + dbt-duckdb | SQL versionado, linhagem, testes e documentação |
| Produto | Streamlit + Plotly | Data app interativo em Python |
| Publicação estática | Jinja + HTML/CSS/JS | Snapshot sem servidor de aplicação |
| Qualidade | pytest, Ruff, mypy, dbt tests | Testes por risco, lint e análise estática |
| Automação | pre-commit + GitHub Actions | Feedback rápido e verificações reproduzíveis |

Todas as ferramentas da aplicação têm opções open source. A decisão e seus limites estão no
[ADR 0001](docs/adr/0001-local-first-open-source-stack.md).

## Licenças

O código-fonte e o painel são distribuídos sob a [licença MIT](LICENSE). Os datasets não estão
cobertos pela MIT: cada edição permanece sob a licença indicada em sua respectiva página no Kaggle.
Consulte [data/LICENSE.md](data/LICENSE.md) antes de usar ou redistribuir dados e derivados.

## Início rápido

Pré-requisito: [uv](https://docs.astral.sh/uv/).

Copie `.env.example` para `.env` e, se quiser autenticar a sincronização, preencha
`KAGGLE_API_TOKEN` com o token gerado em <https://www.kaggle.com/settings/api>. O `.env` é ignorado
pelo Git. Fontes públicas continuam funcionando sem token quando o Kaggle permitir.

```bash
make setup
./scripts/ingest.sh
./scripts/transform.sh
./scripts/build_site.sh
make quality
make dashboard
```

O dashboard abre em `http://localhost:8501`. O `uv.lock` deve entrar no Git e não deve ser editado
manualmente.

Para gerar e servir a versão estática:

```bash
make static
python -m http.server 8000 --directory site
```

Ela abre em `http://localhost:8000` e pode ser hospedada em qualquer serviço de arquivos estáticos.
O build também gera `site/data/state_of_data_public.duckdb`, disponível pelo botão de download da
página. Esse banco público contém somente marts agregados e metadados de origem; o warehouse com
as respostas permanece local.
Veja o [guia de publicação estática](docs/static-site.md).

## Estrutura

```text
analytics/         modelos, testes e documentação dbt
app/               camada de apresentação Streamlit
data/raw/          fontes locais imutáveis e manifesto versionado
data/warehouse/    DuckDB reconstruível e ignorado pelo Git
docs/              decisões, governança e contratos
site/              snapshot estático pronto para publicação
scripts/           etapas executáveis da pipeline
src/state_of_data/ ingestão e regras de infraestrutura
static/            templates e assets-fonte do site estático
tests/             testes rápidos e isolados
```

## Dados e privacidade

Os CSVs não são versionados. A etapa idempotente `state-of-data sources sync` sincroniza os assets
diretamente dos datasets públicos da Data Hackers no Kaggle e só aceita cada arquivo quando o
SHA-256 confere com `data/raw/manifest.json`. O manifesto registra URL, slug, licença, contagem e
checksum por edição. Se o Kaggle publicar uma nova versão, a sincronização falha até que a mudança
seja revisada de forma explícita.

## Pipeline

O GitHub Actions é o orquestrador. O workflow `pages.yml` prepara o ambiente bloqueado pelo
`uv.lock` e executa, em ordem, `scripts/ingest.sh`, `scripts/transform.sh` e
`scripts/build_site.sh`. O artefato resultante só é enviado ao GitHub Pages depois que ingestão,
testes dbt e validações de publicação terminam com sucesso.

`uv` cuida apenas da instalação reproduzível do ambiente. As operações da pipeline chamam os
executáveis instalados em `.venv/bin` diretamente. O workflow pode ser disparado manualmente, por
mudanças relevantes na `main` ou pela verificação mensal do Kaggle.

No GitHub, cadastre `KAGGLE_API_TOKEN` em **Settings → Secrets and variables → Actions → Repository
secrets**. O workflow injeta o secret somente na etapa de ingestão; fontes públicas ainda podem ser
sincronizadas sem ele quando o Kaggle permitir.

Antes de redistribuir dados ou derivados, registre a URL da edição correspondente e confira as
condições exibidas pelo Kaggle. Código e dados são ativos distintos: a licença MIT do painel não
altera nem substitui a licença das fontes.

## Desenvolvimento

Leia [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md) e o
[contrato de dados](docs/data/data-contract.md). Commits seguem Conventional Commits. `git push`
só acontece depois de revisão e autorização explícita da proprietária do projeto.
