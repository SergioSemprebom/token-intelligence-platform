-- ============================================================
-- 09_create_compression_fact.sql
-- Tabela fato (grão: uma linha por registro de public.compactacoes_prompt)
-- ============================================================

CREATE TABLE IF NOT EXISTS analytics.f_compactacoes_prompt (
    compactacao_id         uuid        PRIMARY KEY REFERENCES public.compactacoes_prompt (id),
    data_id                integer     NOT NULL REFERENCES analytics.d_calendario (data_id),
    modelo_id              bigint      NOT NULL REFERENCES analytics.d_modelo (modelo_id),
    origem_id              smallint    NOT NULL REFERENCES analytics.d_origem (origem_id),
    status_id              smallint    NOT NULL REFERENCES analytics.d_status (status_id),
    nivel_id               smallint    NOT NULL REFERENCES analytics.d_nivel_compactacao (nivel_id),
    criado_em              timestamptz NOT NULL,
    encoding_utilizado     varchar(100),
    tokens_originais       integer     NOT NULL DEFAULT 0,
    tokens_compactados     integer     NOT NULL DEFAULT 0,
    tokens_economizados    integer     NOT NULL DEFAULT 0,
    reducao_percentual     numeric(10, 4) NOT NULL DEFAULT 0,
    caracteres_originais   integer,
    caracteres_compactados integer,
    quantidade_alteracoes  integer     NOT NULL DEFAULT 0,
    aprovado               boolean     NOT NULL DEFAULT false,
    compactacao_aplicada   boolean     NOT NULL DEFAULT false,
    fallback_utilizado     boolean     NOT NULL DEFAULT false,
    sucesso                boolean     NOT NULL,
    atualizado_em          timestamptz NOT NULL DEFAULT now()
);

-- Nunca copia texto_original_hash/preview/alteracoes/avisos (JSONB) da tabela
-- operacional para a fato analítica, pelo mesmo motivo de f_processamentos:
-- a fato é destinada ao Power BI e deve evitar texto e blobs semi-estruturados.

CREATE INDEX IF NOT EXISTS ix_f_compactacoes_prompt_data_id     ON analytics.f_compactacoes_prompt (data_id);
CREATE INDEX IF NOT EXISTS ix_f_compactacoes_prompt_modelo_id   ON analytics.f_compactacoes_prompt (modelo_id);
CREATE INDEX IF NOT EXISTS ix_f_compactacoes_prompt_origem_id   ON analytics.f_compactacoes_prompt (origem_id);
CREATE INDEX IF NOT EXISTS ix_f_compactacoes_prompt_status_id   ON analytics.f_compactacoes_prompt (status_id);
CREATE INDEX IF NOT EXISTS ix_f_compactacoes_prompt_nivel_id    ON analytics.f_compactacoes_prompt (nivel_id);
CREATE INDEX IF NOT EXISTS ix_f_compactacoes_prompt_criado_em   ON analytics.f_compactacoes_prompt (criado_em);
CREATE INDEX IF NOT EXISTS ix_f_compactacoes_prompt_aprovado    ON analytics.f_compactacoes_prompt (aprovado);
