# Modelo estrela — camada `analytics`

## Visão geral

A camada `analytics` é um modelo estrela clássico, derivado (nunca copiado
manualmente) da tabela operacional `public.processamentos`. Uma linha em
`analytics.f_processamentos` corresponde a exatamente um registro de
`processamentos`.

Diagrama: [`../diagrams/modelo_estrela.mmd`](../diagrams/modelo_estrela.mmd).

## Tabelas

| Tabela                          | Papel     | Grão / conteúdo                                          |
|----------------------------------|-----------|-----------------------------------------------------------|
| `analytics.d_calendario`         | Dimensão  | Um dia, de 2024-01-01 a 2035-12-31                        |
| `analytics.d_modelo`             | Dimensão  | Um modelo de linguagem distinto solicitado                |
| `analytics.d_operacao`           | Dimensão  | Um tipo de operação (análise, divisão, comparação, custo) |
| `analytics.d_origem`             | Dimensão  | Uma origem da requisição (API, CLI)                        |
| `analytics.d_status`             | Dimensão  | Sucesso ou erro                                            |
| `analytics.f_processamentos`     | Fato      | Um processamento (1:1 com `processamentos`)                |
| `analytics.controle_carga`       | Controle  | Uma execução de `refresh_modelo_analitico()`               |

## Relacionamentos

```
dCalendario[data_id]   1:* fProcessamentos[data_id]
dModelo[modelo_id]     1:* fProcessamentos[modelo_id]
dOperacao[operacao_id] 1:* fProcessamentos[operacao_id]
dOrigem[origem_id]     1:* fProcessamentos[origem_id]
dStatus[status_id]     1:* fProcessamentos[status_id]
```

- Direção de filtro: sempre de dimensão para fato, única direção.
- Não existe relacionamento entre dimensões.
- No Power BI, marque `dCalendario` como tabela de datas usando a coluna `data`.
- Oculte as chaves técnicas (`*_id`) na visualização de relatório; mantenha-as
  visíveis apenas no modelo, para os relacionamentos funcionarem.

## Chaves especiais ("Não informado")

Cada dimensão (exceto `d_calendario`) tem uma linha reservada para quando o
processamento operacional não trouxer aquele dado:

| Dimensão      | Chave especial              |
|---------------|------------------------------|
| `d_modelo`    | `modelo_id = 0`               |
| `d_operacao`  | `operacao_id = 0`, `operacao_codigo = 'nao_informado'` |
| `d_origem`    | `origem_id = 0`, `origem_codigo = 'nao_informado'`     |
| `d_status`    | `status_id = 0`, `status_codigo = 'nao_informado'`     |

A fato nunca fica com uma chave estrangeira nula: `analytics.refresh_modelo_analitico()`
usa `COALESCE(..., 0)` para cair na linha especial quando o dado de origem for nulo
ou não tiver correspondência.

## O que a fato NÃO contém

Por decisão de design (privacidade e tamanho do modelo):

- `texto_preview` (texto do usuário) — não é copiado para a fato.
- `metadados` (JSONB) — não é copiado para a fato.
- Nunca são expostos `token_ids`.

Essas colunas continuam existindo apenas na tabela operacional `processamentos`,
fora do escopo desta camada analítica.

## Carga incremental

`analytics.refresh_modelo_analitico()` (ver
[`../sql/05_create_refresh_functions.sql`](../sql/05_create_refresh_functions.sql))
insere modelos novos, insere fatos novos e atualiza fatos cujo conteúdo mudou,
sem nunca truncar/recarregar a tabela inteira. Cada execução é registrada em
`analytics.controle_carga`.
