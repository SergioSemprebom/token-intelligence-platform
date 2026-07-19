-- ============================================================
-- 08_create_compression_dimension.sql
-- Dimensão de nível de compactação de prompts (Fase 7)
-- ============================================================

CREATE TABLE IF NOT EXISTS analytics.d_nivel_compactacao (
    nivel_id     smallint     PRIMARY KEY,
    nivel_codigo varchar(20)  NOT NULL UNIQUE,
    nivel_nome   varchar(50)  NOT NULL,
    risco        varchar(20)  NOT NULL,
    descricao    varchar(255)
);

INSERT INTO analytics.d_nivel_compactacao (nivel_id, nivel_codigo, nivel_nome, risco, descricao)
VALUES
    (0, 'nao_informado', 'Não informado', 'nenhum', 'Nível de compactação não informado ou desconhecido'),
    (1, 'conservador',   'Conservador',   'baixo',  'Remove apenas espaçamento, pontuação e duplicidades evidentes'),
    (2, 'moderado',      'Moderado',      'medio',  'Simplifica expressões consideradas redundantes'),
    (3, 'agressivo',     'Agressivo',     'alto',   'Reescreve ou remove trechos de forma mais agressiva')
ON CONFLICT (nivel_id) DO NOTHING;
