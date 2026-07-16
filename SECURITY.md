# Segurança

## Dados sensíveis

- Tokens originais permanecem somente no schema local `raw`.
- Marts destinados ao dashboard não incluem respostas individuais.
- Segmentos com menos de 10 respostas são suprimidos.
- CSVs, DuckDB local, `.env` e secrets do Streamlit são ignorados pelo Git.
- Logs registram metadados operacionais, nunca valores de respostas ou credenciais.

Segredos devem entrar por variáveis de ambiente ou GitHub Actions Secrets. Se um segredo chegar ao
histórico Git, ele deve ser revogado e rotacionado; apenas removê-lo do código não é suficiente.

Antes de publicar uma mudança, rode `make audit` e revise consultas, exports e screenshots quanto a
reidentificação. Vulnerabilidades devem ser comunicadas de forma privada à mantenedora, sem abrir
um issue público com dados exploráveis.

