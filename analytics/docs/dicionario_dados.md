# Dicionário de dados — camada `analytics`

## analytics.d_calendario

| Coluna              | Tipo        | Descrição                                          |
|---------------------|-------------|------------------------------------------------------|
| data_id             | integer PK  | Chave no formato `YYYYMMDD`                          |
| data                | date        | Data (única)                                          |
| ano                 | integer     | Ano                                                    |
| semestre            | integer     | 1 ou 2                                                 |
| trimestre           | integer     | 1 a 4                                                  |
| numero_mes          | integer     | 1 a 12 (para ordenação correta do mês)                |
| nome_mes            | varchar     | Nome do mês por extenso, em pt-BR                     |
| nome_mes_curto      | varchar     | Abreviação de 3 letras do mês, em pt-BR               |
| ano_mes             | varchar     | `YYYY-MM`                                              |
| ano_mes_numero      | integer     | `YYYYMM` (para ordenação correta de ano-mês)           |
| dia                 | integer     | Dia do mês                                             |
| dia_semana_numero   | integer     | 0 (domingo) a 6 (sábado)                              |
| nome_dia_semana     | varchar     | Nome do dia da semana em pt-BR                        |
| semana_ano          | integer     | Semana do ano (ISO, via `EXTRACT(WEEK ...)`)          |
| final_semana        | boolean     | `true` para sábado/domingo                             |
| data_inicio_mes     | date        | Primeiro dia do mês da linha                          |
| data_fim_mes        | date        | Último dia do mês da linha                            |

## analytics.d_modelo

| Coluna          | Tipo         | Descrição                                                  |
|-----------------|--------------|--------------------------------------------------------------|
| modelo_id       | bigint PK    | `0` = "Não informado"; demais gerados automaticamente        |
| modelo_nome     | varchar UNIQUE | Nome do modelo, igual a `processamentos.modelo_solicitado`  |
| encoding_padrao | varchar null | Preenchido manualmente se necessário; não inferido           |
| fornecedor      | varchar null | Preenchido manualmente; nunca inventado sem fonte confiável   |
| ativo           | boolean      | Reservado para desativar um modelo sem apagar histórico       |
| criado_em       | timestamptz  | Quando a linha foi criada nesta dimensão                       |
| atualizado_em   | timestamptz  | Quando a linha foi alterada pela última vez                    |

## analytics.d_operacao

| Coluna          | Tipo        | Descrição                                    |
|-----------------|-------------|-------------------------------------------------|
| operacao_id     | smallint PK | `0` = "Não informado"; 1-4 = operações conhecidas |
| operacao_codigo | varchar UNIQUE | Igual a `processamentos.tipo_operacao`        |
| operacao_nome   | varchar     | Nome amigável em pt-BR                          |
| descricao       | varchar     | Descrição da operação                            |
| categoria       | varchar     | Agrupamento (Análise, Processamento, Custos...)  |
| ativo           | boolean     | Reservado para desativar sem apagar histórico     |

## analytics.d_origem

| Coluna        | Tipo        | Descrição                                |
|---------------|-------------|---------------------------------------------|
| origem_id     | smallint PK | `0` = "Não informado"                        |
| origem_codigo | varchar UNIQUE | Igual a `processamentos.origem` (`api`/`cli`) |
| origem_nome   | varchar     | Nome amigável                                |
| descricao     | varchar     | Descrição da origem                          |
| ativo         | boolean     | Reservado para desativar sem apagar histórico |

## analytics.d_status

| Coluna        | Tipo        | Descrição                                    |
|---------------|-------------|--------------------------------------------------|
| status_id     | smallint PK | `0` = "Não informado"                             |
| status_codigo | varchar UNIQUE | `sucesso` / `erro`                             |
| status_nome   | varchar     | Nome amigável                                     |
| sucesso       | boolean     | Espelha `processamentos.sucesso`                  |
| descricao     | varchar     | Descrição do status                               |

## analytics.f_processamentos

Grão: uma linha por registro de `public.processamentos`.

| Coluna                  | Tipo           | Origem / regra                                                       |
|-------------------------|----------------|------------------------------------------------------------------------|
| processamento_id        | uuid PK        | `processamentos.id`                                                    |
| data_id                 | integer FK     | Data (UTC) de `processamentos.criado_em`, no formato `YYYYMMDD`        |
| modelo_id               | bigint FK      | `d_modelo` por `modelo_solicitado`; `0` se nulo/desconhecido           |
| operacao_id             | smallint FK    | `d_operacao` por `tipo_operacao`; `0` se desconhecido                  |
| origem_id               | smallint FK    | `d_origem` por `origem`; `0` se desconhecido                           |
| status_id               | smallint FK    | `d_status` por `sucesso`; `0` se desconhecido                          |
| criado_em               | timestamptz    | Cópia direta                                                            |
| encoding_utilizado      | varchar null   | Cópia direta                                                            |
| fallback_utilizado      | boolean        | Cópia direta                                                            |
| caracteres              | integer null   | Cópia direta                                                            |
| palavras                | integer null   | Cópia direta                                                            |
| bytes_utf8              | integer null   | Cópia direta                                                            |
| tokens_entrada          | integer        | Cópia direta                                                            |
| tokens_saida            | integer        | Cópia direta                                                            |
| total_tokens            | integer        | Cópia direta                                                            |
| quantidade_blocos       | integer null   | Cópia direta (divisão de texto)                                        |
| limite_tokens_bloco     | integer null   | Cópia direta (divisão de texto)                                        |
| sobreposicao_tokens     | integer null   | Cópia direta (divisão de texto)                                        |
| custo_entrada           | numeric(18,6) null | Cópia direta                                                       |
| custo_saida             | numeric(18,6) null | Cópia direta                                                       |
| custo_total             | numeric(18,6) null | Cópia direta                                                       |
| moeda                   | varchar null   | Cópia direta                                                            |
| tempo_processamento_ms  | numeric(18,4) null | Cópia direta                                                       |
| texto_hash              | varchar(64) null | Cópia direta — nunca o texto original                                |
| sucesso                 | boolean        | Cópia direta                                                            |
| possui_erro             | boolean        | `mensagem_erro IS NOT NULL`                                             |
| mensagem_erro           | text null      | Cópia direta                                                            |
| atualizado_em           | timestamptz    | Preenchido pela função de refresh a cada inserção/atualização           |

Colunas de `processamentos` propositalmente **não** copiadas: `texto_preview`,
`metadados` (JSONB).

## analytics.controle_carga

| Coluna                | Tipo         | Descrição                                  |
|------------------------|--------------|-----------------------------------------------|
| carga_id               | bigserial PK | Identificador sequencial da execução           |
| processo               | varchar      | Nome do processo (`refresh_modelo_analitico`)  |
| iniciado_em            | timestamptz  | Início da execução                             |
| finalizado_em          | timestamptz  | Fim da execução                                |
| status                 | varchar      | `sucesso` (a função propaga a exceção em caso de falha, sem gravar linha parcial) |
| registros_inseridos    | integer      | Modelos novos + fatos novos inseridos           |
| registros_atualizados  | integer      | Fatos atualizados                               |
| mensagem               | text         | Resumo em texto da execução                     |
