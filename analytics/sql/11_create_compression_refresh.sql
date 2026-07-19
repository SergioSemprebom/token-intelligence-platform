-- ============================================================
-- 11_create_compression_refresh.sql
-- Carga incremental e idempotente da fato de compactações de prompt.
--
-- analytics.refresh_compactacoes_prompt():
--   1) insere modelos novos (distintos) em analytics.d_modelo (mesma
--      dimensão compartilhada com f_processamentos);
--   2) insere compactações novas em analytics.f_compactacoes_prompt;
--   3) atualiza fatos existentes cujo conteúdo mudou (ex.: aprovação
--      registrada depois da primeira carga), via IS DISTINCT FROM;
--   4) nunca duplica compactacao_id (chave primária + ON CONFLICT);
--   5) registra a execução em analytics.controle_carga, com processo
--      próprio ('refresh_compactacoes_prompt'), sem interferir no
--      registro de analytics.refresh_modelo_analitico();
--   6) é uma função separada da existente, para não alterar a
--      assinatura de analytics.refresh_modelo_analitico().
-- ============================================================

CREATE OR REPLACE FUNCTION analytics.refresh_compactacoes_prompt()
RETURNS TABLE (
    dimensoes_modelo_inseridas integer,
    fatos_inseridos            integer,
    fatos_atualizados          integer,
    executado_em               timestamptz
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_inicio              timestamptz := clock_timestamp();
    v_dimensoes_inseridas integer := 0;
    v_fatos_inseridos     integer := 0;
    v_fatos_atualizados   integer := 0;
    v_mensagem            text;
BEGIN
    WITH novos_modelos AS (
        INSERT INTO analytics.d_modelo (modelo_nome, ativo)
        SELECT DISTINCT cp.modelo_solicitado, true
        FROM public.compactacoes_prompt cp
        WHERE cp.modelo_solicitado IS NOT NULL
        ON CONFLICT (modelo_nome) DO NOTHING
        RETURNING modelo_id
    )
    SELECT COUNT(*)::integer INTO v_dimensoes_inseridas FROM novos_modelos;

    WITH origem_fato AS (
        SELECT
            cp.id AS compactacao_id,
            to_char(cp.criado_em AT TIME ZONE 'UTC', 'YYYYMMDD')::integer AS data_id,
            COALESCE(dm.modelo_id, 0)  AS modelo_id,
            COALESCE(dor.origem_id, 0) AS origem_id,
            COALESCE(dst.status_id, 0) AS status_id,
            COALESCE(dn.nivel_id, 0)   AS nivel_id,
            cp.criado_em,
            cp.encoding_utilizado,
            cp.tokens_originais,
            cp.tokens_compactados,
            cp.tokens_economizados,
            cp.reducao_percentual,
            cp.caracteres_originais,
            cp.caracteres_compactados,
            cp.quantidade_alteracoes,
            cp.aprovado,
            cp.compactacao_aplicada,
            cp.fallback_utilizado,
            cp.sucesso
        FROM public.compactacoes_prompt cp
        LEFT JOIN analytics.d_modelo           dm  ON dm.modelo_nome = cp.modelo_solicitado
        LEFT JOIN analytics.d_origem           dor ON dor.origem_codigo = cp.origem
        LEFT JOIN analytics.d_status           dst ON dst.status_codigo = CASE WHEN cp.sucesso THEN 'sucesso' ELSE 'erro' END
        LEFT JOIN analytics.d_nivel_compactacao dn ON dn.nivel_codigo = cp.nivel_compactacao
    ),
    upsert AS (
        INSERT INTO analytics.f_compactacoes_prompt AS f (
            compactacao_id, data_id, modelo_id, origem_id, status_id, nivel_id,
            criado_em, encoding_utilizado, tokens_originais, tokens_compactados,
            tokens_economizados, reducao_percentual, caracteres_originais,
            caracteres_compactados, quantidade_alteracoes, aprovado,
            compactacao_aplicada, fallback_utilizado, sucesso, atualizado_em
        )
        SELECT
            compactacao_id, data_id, modelo_id, origem_id, status_id, nivel_id,
            criado_em, encoding_utilizado, tokens_originais, tokens_compactados,
            tokens_economizados, reducao_percentual, caracteres_originais,
            caracteres_compactados, quantidade_alteracoes, aprovado,
            compactacao_aplicada, fallback_utilizado, sucesso, now()
        FROM origem_fato
        ON CONFLICT (compactacao_id) DO UPDATE SET
            data_id                = EXCLUDED.data_id,
            modelo_id              = EXCLUDED.modelo_id,
            origem_id              = EXCLUDED.origem_id,
            status_id              = EXCLUDED.status_id,
            nivel_id               = EXCLUDED.nivel_id,
            encoding_utilizado     = EXCLUDED.encoding_utilizado,
            tokens_originais       = EXCLUDED.tokens_originais,
            tokens_compactados     = EXCLUDED.tokens_compactados,
            tokens_economizados    = EXCLUDED.tokens_economizados,
            reducao_percentual     = EXCLUDED.reducao_percentual,
            caracteres_originais   = EXCLUDED.caracteres_originais,
            caracteres_compactados = EXCLUDED.caracteres_compactados,
            quantidade_alteracoes  = EXCLUDED.quantidade_alteracoes,
            aprovado               = EXCLUDED.aprovado,
            compactacao_aplicada   = EXCLUDED.compactacao_aplicada,
            fallback_utilizado     = EXCLUDED.fallback_utilizado,
            sucesso                = EXCLUDED.sucesso,
            atualizado_em          = now()
        WHERE
            (f.data_id, f.modelo_id, f.origem_id, f.status_id, f.nivel_id,
             f.encoding_utilizado, f.tokens_originais, f.tokens_compactados,
             f.tokens_economizados, f.reducao_percentual, f.caracteres_originais,
             f.caracteres_compactados, f.quantidade_alteracoes, f.aprovado,
             f.compactacao_aplicada, f.fallback_utilizado, f.sucesso)
            IS DISTINCT FROM
            (EXCLUDED.data_id, EXCLUDED.modelo_id, EXCLUDED.origem_id, EXCLUDED.status_id,
             EXCLUDED.nivel_id, EXCLUDED.encoding_utilizado, EXCLUDED.tokens_originais,
             EXCLUDED.tokens_compactados, EXCLUDED.tokens_economizados,
             EXCLUDED.reducao_percentual, EXCLUDED.caracteres_originais,
             EXCLUDED.caracteres_compactados, EXCLUDED.quantidade_alteracoes,
             EXCLUDED.aprovado, EXCLUDED.compactacao_aplicada, EXCLUDED.fallback_utilizado,
             EXCLUDED.sucesso)
        RETURNING (xmax = 0) AS foi_inserido
    )
    SELECT
        COALESCE(COUNT(*) FILTER (WHERE foi_inserido), 0)::integer,
        COALESCE(COUNT(*) FILTER (WHERE NOT foi_inserido), 0)::integer
    INTO v_fatos_inseridos, v_fatos_atualizados
    FROM upsert;

    v_mensagem := format(
        'Refresh de compactações concluído: %s modelo(s) novo(s) em d_modelo, %s fato(s) inserido(s), %s fato(s) atualizado(s).',
        v_dimensoes_inseridas, v_fatos_inseridos, v_fatos_atualizados
    );

    INSERT INTO analytics.controle_carga (
        processo, iniciado_em, finalizado_em, status,
        registros_inseridos, registros_atualizados, mensagem
    ) VALUES (
        'refresh_compactacoes_prompt', v_inicio, clock_timestamp(), 'sucesso',
        v_dimensoes_inseridas + v_fatos_inseridos, v_fatos_atualizados, v_mensagem
    );

    RETURN QUERY
    SELECT v_dimensoes_inseridas, v_fatos_inseridos, v_fatos_atualizados, clock_timestamp();
END;
$$;

COMMENT ON FUNCTION analytics.refresh_compactacoes_prompt() IS
    'Carga incremental e idempotente de analytics.f_compactacoes_prompt a partir '
    'de public.compactacoes_prompt. Função separada de refresh_modelo_analitico(), '
    'não altera f_processamentos nem seu processo de carga.';
