# Dashboard State of Data Brasil

Uma leitura das pesquisas State of Data Brazil de 2021 a 2025. O painel reúne resultados sobre
perfil, carreira, trabalho e tecnologias usadas por profissionais de dados no Brasil.

Este é um projeto da [Profa. Artemisia Weyl](https://github.com/arteweyl), feito a partir dos dados
públicos disponibilizados pela Data Hackers no Kaggle.

Há duas formas de consultar os resultados:

- um dashboard interativo em Streamlit;
- uma página estática, que também oferece para download um banco DuckDB com as tabelas agregadas.

## Rodando localmente

Você precisa ter o [uv](https://docs.astral.sh/uv/) instalado.

```bash
make setup
./scripts/ingest.sh
./scripts/transform.sh
make dashboard
```

O dashboard estará em <http://localhost:8501>.

Para gerar e servir a página estática:

```bash
./scripts/build_site.sh
python -m http.server 8000 --directory site
```

Depois, acesse <http://localhost:8000>.

## Acesso ao Kaggle

Copie `.env.example` para `.env` e adicione seu token:

```dotenv
KAGGLE_API_TOKEN=seu_token_aqui
```

O token pode ser criado em <https://www.kaggle.com/settings/api>. O arquivo `.env` não entra no
Git. Quando o Kaggle permite acesso público sem autenticação, a sincronização também funciona sem
o token.

## Como os dados são atualizados

A atualização tem três etapas:

1. `scripts/ingest.sh` baixa os arquivos do Kaggle e confere os checksums registrados no manifesto;
2. `scripts/transform.sh` executa os modelos e testes do dbt;
3. `scripts/build_site.sh` gera a página estática e o DuckDB público.

O GitHub Actions executa essas etapas na publicação e na verificação mensal das fontes. O `uv` é
usado somente para instalar o ambiente definido pelo `uv.lock`.

Os arquivos originais e o warehouse completo ficam fora do Git. O DuckDB publicado contém apenas
resultados agregados e metadados das fontes, sem respostas individuais.

## Tecnologias

- DuckDB para armazenamento e consultas analíticas;
- dbt Core com dbt-duckdb para transformação e testes;
- Streamlit e Plotly para o dashboard interativo;
- Jinja, HTML, CSS e JavaScript para a versão estática;
- pytest, Ruff e mypy para qualidade do código;
- GitHub Actions para automação e publicação.

Mais detalhes sobre essa escolha estão no
[ADR 0001](docs/adr/0001-local-first-open-source-stack.md).

## Estrutura do repositório

```text
analytics/         modelos e testes dbt
app/               dashboard Streamlit
data/raw/          manifesto e arquivos obtidos do Kaggle
data/warehouse/    banco DuckDB local
docs/              decisões e documentação dos dados
scripts/           etapas da pipeline
src/state_of_data/ código Python do projeto
static/            templates e assets da página estática
tests/             testes automatizados
```

O diretório `site/` é criado durante o build e não é versionado.

## Licenças

O código e a interface estão sob a [licença MIT](LICENSE).

Os dados mantêm as licenças definidas em cada edição da pesquisa: Creative Commons entre 2021 e
2023 e Open Database em 2024 e 2025. Consulte [data/LICENSE.md](data/LICENSE.md) antes de
redistribuir os dados ou seus derivados.

## Desenvolvimento

Para rodar todas as verificações locais:

```bash
make quality
```

As orientações para contribuir estão em [CONTRIBUTING.md](CONTRIBUTING.md). Questões de segurança
devem seguir [SECURITY.md](SECURITY.md).
