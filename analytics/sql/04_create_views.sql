-- ============================================================
-- 04_create_views.sql
-- Views de consumo estáveis para o Power BI.
-- ============================================================

-- ----------------------------------------------------------
-- analytics.vw_powerbi_processamentos
-- Granularidade: um processamento por linha, com nomes amigáveis.
-- ----------------------------------------------------------
CREATE OR REPLACE VIEW analytics.vw_powerbi_processamentos AS
SELECT
    f.processamento_id,
    c.data,
    f.criado_em,
    c.ano,
    c.trimestre,
    c.numero_mes,
    c.nome_mes,
    c.ano_mes,
    m.modelo_nome        AS modelo,
    f.encoding_utilizado AS encoding,
    o.operacao_nome      AS tipo_operacao,
    org.origem_nome      AS origem,
    st.status_nome       AS status,
    f.fallback_utilizado,
    f.caracteres,
    f.palavras,
    f.bytes_utf8,
    f.tokens_entrada,
    f.tokens_saida,
    f.total_tokens,
    f.quantidade_blocos,
    f.limite_tokens_bloco,
    f.sobreposicao_tokens,
    f.custo_entrada,
    f.custo_saida,
    f.custo_total,
    f.moeda,
    f.tempo_processamento_ms,
    f.texto_hash,
    f.sucesso,
    f.possui_erro
FROM analytics.f_processamentos f
JOIN analytics.d_calendario c ON c.data_id = f.data_id
JOIN analytics.d_modelo    m ON m.modelo_id = f.modelo_id
JOIN analytics.d_operacao  o ON o.operacao_id = f.operacao_id
JOIN analytics.d_origem  org ON org.origem_id = f.origem_id
JOIN analytics.d_status   st ON st.status_id = f.status_id;

-- ----------------------------------------------------------
-- analytics.vw_powerbi_resumo_diario
-- ----------------------------------------------------------
CREATE OR REPLACE VIEW analytics.vw_powerbi_resumo_diario AS
SELECT
    c.data,
    m.modelo_nome   AS modelo,
    o.operacao_nome AS tipo_operacao,
    org.origem_nome AS origem,
    st.status_nome  AS status,
    COUNT(*)                                     AS quantidade_processamentos,
    COALESCE(SUM(f.tokens_entrada), 0)           AS tokens_entrada,
    COALESCE(SUM(f.tokens_saida), 0)             AS tokens_saida,
    COALESCE(SUM(f.total_tokens), 0)             AS total_tokens,
    COALESCE(SUM(f.custo_total), 0)              AS custo_total,
    COALESCE(SUM(f.tempo_processamento_ms), 0)   AS tempo_total_ms,
    COALESCE(AVG(f.tempo_processamento_ms), 0)   AS tempo_medio_ms,
    COUNT(*) FILTER (WHERE f.sucesso)            AS quantidade_sucessos,
    COUNT(*) FILTER (WHERE NOT f.sucesso)        AS quantidade_erros,
    COUNT(*) FILTER (WHERE f.fallback_utilizado) AS quantidade_fallbacks
FROM analytics.f_processamentos f
JOIN analytics.d_calendario c ON c.data_id = f.data_id
JOIN analytics.d_modelo    m ON m.modelo_id = f.modelo_id
JOIN analytics.d_operacao  o ON o.operacao_id = f.operacao_id
JOIN analytics.d_origem  org ON org.origem_id = f.origem_id
JOIN analytics.d_status   st ON st.status_id = f.status_id
GROUP BY c.data, m.modelo_nome, o.operacao_nome, org.origem_nome, st.status_nome;

-- ----------------------------------------------------------
-- analytics.vw_powerbi_resumo_mensal
-- ----------------------------------------------------------
CREATE OR REPLACE VIEW analytics.vw_powerbi_resumo_mensal AS
SELECT
    c.ano,
    c.numero_mes,
    c.nome_mes,
    c.ano_mes,
    m.modelo_nome   AS modelo,
    o.operacao_nome AS tipo_operacao,
    COUNT(*)                                   AS quantidade_processamentos,
    COALESCE(SUM(f.total_tokens), 0)           AS total_tokens,
    COALESCE(SUM(f.custo_total), 0)            AS custo_total,
    COALESCE(AVG(f.tempo_processamento_ms), 0) AS tempo_medio_ms,
    CASE WHEN COUNT(*) = 0 THEN 0
         ELSE COUNT(*) FILTER (WHERE f.sucesso)::numeric / COUNT(*)
    END                                         AS taxa_sucesso,
    COUNT(*) FILTER (WHERE f.fallback_utilizado) AS quantidade_fallbacks
FROM analytics.f_processamentos f
JOIN analytics.d_calendario c ON c.data_id = f.data_id
JOIN analytics.d_modelo    m ON m.modelo_id = f.modelo_id
JOIN analytics.d_operacao  o ON o.operacao_id = f.operacao_id
GROUP BY c.ano, c.numero_mes, c.nome_mes, c.ano_mes, m.modelo_nome, o.operacao_nome;

-- ----------------------------------------------------------
-- analytics.vw_powerbi_textos_repetidos
-- Apenas hashes que aparecem em mais de um processamento.
-- ----------------------------------------------------------
CREATE OR REPLACE VIEW analytics.vw_powerbi_textos_repetidos AS
SELECT
    texto_hash,
    COUNT(*)                       AS quantidade_processamentos,
    MIN(criado_em)                 AS primeiro_processamento,
    MAX(criado_em)                 AS ultimo_processamento,
    COALESCE(SUM(total_tokens), 0) AS total_tokens,
    COALESCE(SUM(custo_total), 0)  AS custo_total
FROM analytics.f_processamentos
WHERE texto_hash IS NOT NULL
GROUP BY texto_hash
HAVING COUNT(*) > 1;
