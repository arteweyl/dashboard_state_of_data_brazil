# Site estático

O diretório `site/` é um snapshot pré-renderizado e pode ser servido por GitHub Pages, Netlify,
Cloudflare Pages, S3 ou qualquer servidor HTTP. Ele não precisa de Python ou Streamlit em
produção.

## Contrato de publicação

- A origem são somente os marts agregados `annual_summary`, `categorical_distribution`,
  `data_quality` e `technology_cloud`.
- A exportação falha se encontrar nomes de identificadores, tokens ou tabelas brutas no HTML.
- Categorias com menos de 10 respostas já foram removidas na camada dbt.
- `snapshot.json` registra versão, horário, anos, total harmonizado, limiar de privacidade e hash do
  manifesto das fontes.
- `data/state_of_data_public.duckdb` contém somente os quatro marts autorizados em `analytics` e a
  proveniência/licença das edições em `metadata`; schemas brutos e respostas individuais não entram.
- `site/` é um artefato gerado e não é versionado. O GitHub Actions o constrói novamente a partir
  das fontes contratadas antes de enviá-lo ao GitHub Pages.

## Gerar e revisar

Depois de reconstruir o warehouse e os marts:

```bash
make static
python -m http.server 8000 --directory site
```

Abra `http://localhost:8000`. Para um build com timestamp determinístico, defina
`SOURCE_DATE_EPOCH` com um Unix timestamp antes de executar o comando.

Toda alteração em dados, transformação, template ou assets deve passar pelo workflow completo. Não
edite `site/index.html` manualmente; altere os arquivos em `static/` e execute novamente o gerador.

Exemplo de consulta ao arquivo publicado no CLI do DuckDB:

```sql
ATTACH 'site/data/state_of_data_public.duckdb' AS sod (READ_ONLY);
FROM sod.analytics.annual_summary;
```

## GitHub Pages

O workflow `pages.yml` sincroniza e ingere as fontes, executa o dbt, constrói `site/`, envia o
artefato e então o publica. Ele roda manualmente, mensalmente e quando componentes da pipeline mudam
na branch `main`. O repositório precisa ter GitHub Pages configurado com **GitHub Actions** como
fonte. A publicação só deve ocorrer depois da revisão e de autorização explícita para o `git push`.
