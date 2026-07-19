-- ============================================================
-- 10_create_compression_views.sql
-- Views de consumo estáveis para o Power BI (compactação de prompts)
-- ============================================================

-- ----------------------------------------------------------
-- analytics.vw_powerbi_compactacoes
-- Granularidade: uma compactação por linha, com nomes amigáveis.
-- ----------------------------------------------------------
CREATE OR REPLACE VIEW analytics.vw_powerbi_compactacoes AS
SELECT
    f.compactacao_id,
    c.data,
    f.criado_em,
    c.ano,
    c.trimestre,
    c.numero_mes,
    c.nome_mes,
    c.ano_mes,
    m.modelo_nome    AS modelo,
    f.encoding_utilizado AS encoding,
    n.nivel_nome     AS nivel_compactacao,
    n.risco,
    org.origem_nome  AS origem,
    st.status_nome   AS status,
    f.tokens_originais,
    f.tokens_compactados,
    f.tokens_economizados,
    f.reducao_percentual,
    f.caracteres_originais,
    f.caracteres_compactados,
    f.quantidade_alteracoes,
    f.aprovado,
    f.compactacao_aplicada,
    f.fallback_utilizado,
    f.sucesso
FROM analytics.f_compactacoes_prompt f
JOIN analytics.d_calendario        c   ON c.data_id = f.data_id
JOIN analytics.d_modelo            m   ON m.modelo_id = f.modelo_id
JOIN analytics.d_origem            org ON org.origem_id = f.origem_id
JOIN analytics.d_status            st  ON st.status_id = f.status_id
JOIN analytics.d_nivel_compactacao  n  ON n.nivel_id = f.nivel_id;

-- ----------------------------------------------------------
-- analytics.vw_powerbi_resumo_compactacao_diario
-- ----------------------------------------------------------
CREATE OR REPLACE VIEW analytics.vw_powerbi_resumo_compactacao_diario AS
SELECT
    c.data,
    m.modelo_nome   AS modelo,
    n.nivel_nome    AS nivel_compactacao,
    org.origem_nome AS origem,
    COUNT(*)                                              AS quantidade_compactacoes,
    COALESCE(SUM(f.tokens_originais), 0)                  AS tokens_originais,
    COALESCE(SUM(f.tokens_compactados), 0)                AS tokens_compactados,
    COALESCE(SUM(f.tokens_economizados), 0)                AS tokens_economizados,
    COALESCE(AVG(f.reducao_percentual), 0)                AS reducao_media_percentual,
    COUNT(*) FILTER (WHERE f.aprovado)                    AS quantidade_aprovadas,
    CASE WHEN COUNT(*) = 0 THEN 0
         ELSE COUNT(*) FILTER (WHERE f.aprovado)::numeric / COUNT(*)
    END                                                     AS taxa_aprovacao,
    COUNT(*) FILTER (WHERE NOT f.compactacao_aplicada)     AS compactacoes_sem_beneficio
FROM analytics.f_compactacoes_prompt f
JOIN analytics.d_calendario       c   ON c.data_id = f.data_id
JOIN analytics.d_modelo           m   ON m.modelo_id = f.modelo_id
JOIN analytics.d_origem           org ON org.origem_id = f.origem_id
JOIN analytics.d_nivel_compactacao n  ON n.nivel_id = f.nivel_id
GROUP BY c.data, m.modelo_nome, n.nivel_nome, org.origem_nome;

-- ----------------------------------------------------------
-- analytics.vw_powerbi_resumo_compactacao_mensal
-- ----------------------------------------------------------
CREATE OR REPLACE VIEW analytics.vw_powerbi_resumo_compactacao_mensal AS
SELECT
    c.ano,
    c.numero_mes,
    c.nome_mes,
    c.ano_mes,
    m.modelo_nome   AS modelo,
    n.nivel_nome    AS nivel_compactacao,
    org.origem_nome AS origem,
    COUNT(*)                                              AS quantidade_compactacoes,
    COALESCE(SUM(f.tokens_originais), 0)                  AS tokens_originais,
    COALESCE(SUM(f.tokens_compactados), 0)                AS tokens_compactados,
    COALESCE(SUM(f.tokens_economizados), 0)                AS tokens_economizados,
    COALESCE(AVG(f.reducao_percentual), 0)                AS reducao_media_percentual,
    COUNT(*) FILTER (WHERE f.aprovado)                    AS quantidade_aprovadas,
    CASE WHEN COUNT(*) = 0 THEN 0
         ELSE COUNT(*) FILTER (WHERE f.aprovado)::numeric / COUNT(*)
    END                                                     AS taxa_aprovacao,
    COUNT(*) FILTER (WHERE NOT f.compactacao_aplicada)     AS compactacoes_sem_beneficio
FROM analytics.f_compactacoes_prompt f
JOIN analytics.d_calendario       c   ON c.data_id = f.data_id
JOIN analytics.d_modelo           m   ON m.modelo_id = f.modelo_id
JOIN analytics.d_origem           org ON org.origem_id = f.origem_id
JOIN analytics.d_nivel_compactacao n  ON n.nivel_id = f.nivel_id
GROUP BY c.ano, c.numero_mes, c.nome_mes, c.ano_mes, m.modelo_nome, n.nivel_nome, org.origem_nome;
