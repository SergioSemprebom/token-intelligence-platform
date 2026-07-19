-- ============================================================
-- 07_powerbi_source_queries.sql
-- Consultas individuais para uso em "Obter Dados > Banco de Dados
-- PostgreSQL > Consulta SQL" no Power BI. Cada consulta traz apenas
-- as colunas necessárias, com nomes já amigáveis para o modelo.
--
-- Alternativa recomendada: importar as tabelas/views diretamente pelo
-- navegador do Power BI (ver analytics/docs/guia_conexao_powerbi.md) —
-- estas consultas servem para quem prefere "Consulta SQL" nativa.
-- ============================================================

-- dCalendario
SELECT
    data_id,
    data,
    ano,
    semestre,
    trimestre,
    numero_mes,
    nome_mes,
    nome_mes_curto,
    ano_mes,
    ano_mes_numero,
    dia,
    dia_semana_numero,
    nome_dia_semana,
    semana_ano,
    final_semana,
    data_inicio_mes,
    data_fim_mes
FROM analytics.d_calendario;

-- dModelo
SELECT
    modelo_id,
    modelo_nome,
    encoding_padrao,
    fornecedor,
    ativo
FROM analytics.d_modelo;

-- dOperacao
SELECT
    operacao_id,
    operacao_codigo,
    operacao_nome,
    descricao,
    categoria,
    ativo
FROM analytics.d_operacao;

-- dOrigem
SELECT
    origem_id,
    origem_codigo,
    origem_nome,
    descricao,
    ativo
FROM analytics.d_origem;

-- dStatus
SELECT
    status_id,
    status_codigo,
    status_nome,
    sucesso,
    descricao
FROM analytics.d_status;

-- fProcessamentos
SELECT
    processamento_id,
    data_id,
    modelo_id,
    operacao_id,
    origem_id,
    status_id,
    criado_em,
    encoding_utilizado,
    fallback_utilizado,
    caracteres,
    palavras,
    bytes_utf8,
    tokens_entrada,
    tokens_saida,
    total_tokens,
    quantidade_blocos,
    limite_tokens_bloco,
    sobreposicao_tokens,
    custo_entrada,
    custo_saida,
    custo_total,
    moeda,
    tempo_processamento_ms,
    texto_hash,
    sucesso,
    possui_erro
FROM analytics.f_processamentos;

-- Resumo diário (já agregado — útil para relatórios mais leves)
SELECT * FROM analytics.vw_powerbi_resumo_diario;

-- Resumo mensal
SELECT * FROM analytics.vw_powerbi_resumo_mensal;

-- Textos repetidos (auditoria)
SELECT * FROM analytics.vw_powerbi_textos_repetidos;

-- Processamentos detalhados, já com nomes de dimensão resolvidos
-- (alternativa a importar a fato + as 5 dimensões separadamente)
SELECT * FROM analytics.vw_powerbi_processamentos;
