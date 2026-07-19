-- ============================================================
-- 03_create_fact.sql
-- Tabela fato (grão: uma linha por registro de public.processamentos)
-- e tabela de controle de carga.
-- ============================================================

CREATE TABLE IF NOT EXISTS analytics.f_processamentos (
    processamento_id       uuid        PRIMARY KEY REFERENCES public.processamentos (id),
    data_id                integer     NOT NULL REFERENCES analytics.d_calendario (data_id),
    modelo_id              bigint      NOT NULL REFERENCES analytics.d_modelo (modelo_id),
    operacao_id            smallint    NOT NULL REFERENCES analytics.d_operacao (operacao_id),
    origem_id              smallint    NOT NULL REFERENCES analytics.d_origem (origem_id),
    status_id              smallint    NOT NULL REFERENCES analytics.d_status (status_id),
    criado_em              timestamptz NOT NULL,
    encoding_utilizado     varchar(100),
    fallback_utilizado     boolean     NOT NULL DEFAULT false,
    caracteres             integer,
    palavras               integer,
    bytes_utf8             integer,
    tokens_entrada         integer     NOT NULL DEFAULT 0,
    tokens_saida           integer     NOT NULL DEFAULT 0,
    total_tokens           integer     NOT NULL DEFAULT 0,
    quantidade_blocos      integer,
    limite_tokens_bloco    integer,
    sobreposicao_tokens    integer,
    custo_entrada          numeric(18, 6),
    custo_saida            numeric(18, 6),
    custo_total            numeric(18, 6),
    moeda                  varchar(10),
    tempo_processamento_ms numeric(18, 4),
    texto_hash             varchar(64),
    sucesso                boolean     NOT NULL,
    possui_erro            boolean     NOT NULL,
    mensagem_erro          text,
    atualizado_em          timestamptz NOT NULL DEFAULT now()
);

-- texto_preview e metadados (JSONB) da tabela operacional propositalmente
-- NÃO são copiados para a fato analítica: a fato é destinada ao Power BI e
-- deve evitar texto de usuário e blobs semi-estruturados.

CREATE INDEX IF NOT EXISTS ix_f_processamentos_data_id            ON analytics.f_processamentos (data_id);
CREATE INDEX IF NOT EXISTS ix_f_processamentos_modelo_id          ON analytics.f_processamentos (modelo_id);
CREATE INDEX IF NOT EXISTS ix_f_processamentos_operacao_id        ON analytics.f_processamentos (operacao_id);
CREATE INDEX IF NOT EXISTS ix_f_processamentos_origem_id          ON analytics.f_processamentos (origem_id);
CREATE INDEX IF NOT EXISTS ix_f_processamentos_status_id          ON analytics.f_processamentos (status_id);
CREATE INDEX IF NOT EXISTS ix_f_processamentos_criado_em          ON analytics.f_processamentos (criado_em);
CREATE INDEX IF NOT EXISTS ix_f_processamentos_texto_hash         ON analytics.f_processamentos (texto_hash);
CREATE INDEX IF NOT EXISTS ix_f_processamentos_fallback_utilizado ON analytics.f_processamentos (fallback_utilizado);
CREATE INDEX IF NOT EXISTS ix_f_processamentos_sucesso            ON analytics.f_processamentos (sucesso);

-- ----------------------------------------------------------
-- analytics.controle_carga
-- Registra cada execução de analytics.refresh_modelo_analitico().
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS analytics.controle_carga (
    carga_id              bigserial   PRIMARY KEY,
    processo              varchar(100) NOT NULL,
    iniciado_em           timestamptz NOT NULL,
    finalizado_em         timestamptz,
    status                varchar(20) NOT NULL,
    registros_inseridos   integer     NOT NULL DEFAULT 0,
    registros_atualizados integer     NOT NULL DEFAULT 0,
    mensagem              text
);

CREATE INDEX IF NOT EXISTS ix_controle_carga_iniciado_em ON analytics.controle_carga (iniciado_em);
