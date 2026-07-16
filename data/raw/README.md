# Dados brutos

Esta pasta recebe os CSVs originais do State of Data. Os arquivos são imutáveis e não entram
no Git: além do volume, contêm identificadores pseudônimos que não são necessários no produto.

O arquivo `manifest.json` registra nome, ano, slug e URL do Kaggle, licença declarada, quantidade
esperada de linhas e SHA-256 de cada fonte. A ingestão falha se um arquivo estiver ausente ou tiver
sido alterado silenciosamente.

Não publique arquivos brutos ou registros individuais. Antes de redistribuir dados ou derivados,
consulte `data/LICENSE.md`, confirme a licença da edição no Kaggle e preserve a atribuição exigida
pela fonte.

Para sincronizar as fontes e carregá-las no DuckDB, execute `./scripts/ingest.sh` depois de preparar
o ambiente com `uv sync --all-groups --locked`.
Arquivos já válidos não são baixados novamente. Um arquivo divergente nunca é sobrescrito sem
`--force`, e mesmo com essa opção o novo conteúdo só é aceito se corresponder ao checksum aprovado.

Autenticação opcional: copie `.env.example` para `.env` e informe `KAGGLE_API_TOKEN`. O processo
prioriza a variável já exportada no ambiente, não registra o token em logs e remove o cabeçalho de
autorização quando o Kaggle redireciona o download para outro domínio.
