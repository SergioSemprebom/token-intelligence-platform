# Indicadores e páginas sugeridas do Power BI

## Indicadores cobertos pelo modelo

| # | Indicador                              | Como obter                                                       |
|---|------------------------------------------|-------------------------------------------------------------------|
| 1 | Total de processamentos                   | Medida `Total Processamentos`                                     |
| 2 | Tokens de entrada                         | Medida `Tokens Entrada`                                            |
| 3 | Tokens de saída                           | Medida `Tokens Saída`                                              |
| 4 | Total de tokens                           | Medida `Total Tokens`                                              |
| 5 | Custo de entrada                          | Medida `Custo Entrada`                                             |
| 6 | Custo de saída                            | Medida `Custo Saída`                                               |
| 7 | Custo total                               | Medida `Custo Total`                                               |
| 8 | Tempo médio de processamento              | Medida `Tempo Médio Processamento (ms)`                            |
| 9 | Taxa de sucesso                           | Medida `Taxa de Sucesso %`                                         |
| 10 | Quantidade de erros                      | Medida `Processamentos com Erro`                                   |
| 11 | Operações por período                    | `fProcessamentos` + `dCalendario`, ou `vw_powerbi_resumo_diario`/`_mensal` |
| 12 | Consumo por modelo                       | `fProcessamentos` + `dModelo`                                      |
| 13 | Consumo por tipo de operação              | `fProcessamentos` + `dOperacao`                                     |
| 14 | Consumo por origem                        | `fProcessamentos` + `dOrigem`                                       |
| 15 | Uso de fallback                           | Medidas `Fallbacks Utilizados` / `Taxa de Fallback %`               |
| 16 | Textos repetidos pelo hash                | `analytics.vw_powerbi_textos_repetidos`                             |
| 17 | Quantidade e tamanho dos blocos           | `fProcessamentos[quantidade_blocos]`, `[limite_tokens_bloco]`       |
| 18 | Tendência diária e mensal                 | `vw_powerbi_resumo_diario` / `vw_powerbi_resumo_mensal`             |
| 19 | Custo médio por processamento             | Medida `Custo Médio por Processamento`                              |
| 20 | Tokens médios por processamento           | Medida `Tokens Médios por Processamento`                            |

## Páginas sugeridas

### 1. Visão Executiva

**Cards:** Total Processamentos · Total Tokens · Custo Total · Taxa de Sucesso % ·
Tempo Médio Processamento (ms) · Taxa de Fallback %.

**Gráficos:**
- Processamentos por mês (linha) — `dCalendario[ano_mes]` × `[Total Processamentos]`.
- Tokens por mês (linha ou colunas) — `dCalendario[ano_mes]` × `[Total Tokens]`.
- Custo por modelo (barras) — `dModelo[modelo_nome]` × `[Custo Total]`.
- Processamentos por operação (pizza ou barras) — `dOperacao[operacao_nome]` × `[Total Processamentos]`.

### 2. Tokens e Custos

- Tokens de entrada vs. saída (colunas empilhadas) — `[Tokens Entrada]`, `[Tokens Saída]`.
- Custo por modelo (barras) — `dModelo[modelo_nome]` × `[Custo Total]`.
- Custo por operação (barras) — `dOperacao[operacao_nome]` × `[Custo Total]`.
- Custo médio por processamento (card/KPI) — `[Custo Médio por Processamento]`.
- Tendência diária (linha) — `dCalendario[data]` × `[Custo Total]`.
- Ranking de modelos (tabela ordenada por `[Total Tokens]` ou `[Custo Total]`).

### 3. Desempenho e Qualidade

- Tempo médio (card) — `[Tempo Médio Processamento (ms)]`.
- Taxa de sucesso (gauge/card) — `[Taxa de Sucesso %]`.
- Erros por operação (barras) — `dOperacao[operacao_nome]` × `[Processamentos com Erro]`.
- Fallback por modelo (barras) — `dModelo[modelo_nome]` × `[Fallbacks Utilizados]`.
- Operações mais lentas (tabela ordenada por `[Tempo Médio Processamento (ms)]`).
- Distribuição do tempo de processamento (histograma sobre `fProcessamentos[tempo_processamento_ms]`).

### 4. Auditoria

- Tabela detalhada de processamentos — baseada em `vw_powerbi_processamentos` (ou
  `fProcessamentos` + dimensões), com filtros (slicers) por data, modelo, operação,
  origem e status.
- Textos repetidos pelo hash — `vw_powerbi_textos_repetidos`.
- Mensagens de erro — `fProcessamentos[mensagem_erro]` filtrado por `possui_erro = true`.
- Registros com fallback — `fProcessamentos` filtrado por `fallback_utilizado = true`.

## Formatação recomendada

- Custos: formato moeda.
- Taxas (`Taxa de Sucesso %`, `Taxa de Erro %`, `Taxa de Fallback %`, `Variação % `): percentual.
- Tokens e contagens: número inteiro.
- Tempo de processamento: milissegundos, 2 casas decimais.
