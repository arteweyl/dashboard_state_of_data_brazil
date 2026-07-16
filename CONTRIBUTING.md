# Contribuindo

## Fluxo local

1. Defina problema, usuário, hipótese e critério de aceitação no issue ou PR.
2. Crie uma branch curta a partir de `main`.
3. Faça uma mudança coesa e acrescente testes proporcionais ao risco.
4. Execute `make quality`; para alterações de dados, execute também ingestão e `make transform`.
5. Atualize documentação e ADRs quando comportamento ou decisões mudarem.
6. Use commits Conventional Commits, por exemplo `feat: add salary trend mart`.

Pull requests devem explicar comportamento, evidências de teste, riscos de privacidade, impacto em
schemas e estratégia de rollback. Cobertura é um sinal; testes devem proteger comportamento.

Não inclua CSVs brutos, warehouses, credenciais, tokens, respostas individuais ou artefatos de
build. Nunca execute `git push` sem revisão e autorização explícita da proprietária.

