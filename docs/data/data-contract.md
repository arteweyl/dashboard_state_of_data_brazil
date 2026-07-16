# Contrato de dados

## Entrada

Cada edição precisa ter no manifesto: `year`, nome exato do arquivo, quantidade de registros,
SHA-256, `kaggle_ref`, `source_url` e licença declarada no Kaggle. A sincronização aceita somente
slugs sob `datahackers/` e só promove o arquivo temporário quando o checksum confere. A ingestão aceita
CSV UTF-8 com header, lê inicialmente todas as colunas como texto e falha
se checksum ou contagem divergir.

Os headers são normalizados de forma determinística para ASCII `snake_case`; colisões recebem
sufixos. Nenhum valor é alterado na camada `raw`.

## Camada harmonizada

`stg_survey__respondents` oferece dimensões comuns e preserva `null` quando uma edição não perguntou
um atributo. Idade inválida fica fora do modelo. O identificador original é substituído por hash com
namespace do ano, usado apenas em validações internas. As fontes contratadas contêm 8 pares de
linhas totalmente idênticas (2021, 2022, 2024 e 2025); o staging mantém deterministicamente uma
linha de cada par e testa o total harmonizado de 20.913 respostas.

Para gestores, o questionário registra o cargo em um campo próprio e deixa o campo de cargo geral
vazio. O staging aplica uma atribuição lógica: usa o cargo de gestão quando o cargo geral não existe
e classifica a senioridade como `Gestão`. A coluna `role_was_harmonized` preserva a rastreabilidade
dessa regra; não se trata de imputação estatística.

## Camada de consumo

`annual_summary` contém apenas indicadores anuais. `survey_overview` agrega dimensões categóricas e
suprime células com menos de 10 respostas. O app só pode consultar esses marts allow-listed.
Percentuais de satisfação usam apenas respostas não nulas; ausência de resposta não é interpretada
como insatisfação.

## Tratamento de dados ausentes

Ausências são classificadas antes do cálculo:

- `Não perguntado`: a pergunta não existia naquela edição;
- `Não aplicável`: o fluxo do questionário não exigia resposta daquela pessoa;
- `Sem resposta`: a pessoa era elegível, mas não há resposta válida;
- atribuição lógica: outro campo do próprio questionário determina a resposta sem ambiguidade, como
  o cargo específico de gestores preenchendo o cargo geral.

O mart `data_quality` publica, por pergunta e edição, o total de participantes, elegíveis, respostas
válidas, ausências, não aplicáveis e a taxa de cobertura. O dashboard não aplica imputação
estatística: as fontes não fornecem pesos amostrais, modelos validados ou flags de imputação que
permitam estimar respostas mantendo rastreabilidade e incerteza adequadas.

Mudanças incompatíveis exigem novo ADR, atualização de testes, documentação da migração e plano de
rollback. Alterar um CSV existente exige revisar a fonte e atualizar explicitamente seu contrato;
nunca se aceita drift silencioso.
