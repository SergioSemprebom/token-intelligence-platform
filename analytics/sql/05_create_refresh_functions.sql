-- ============================================================
-- 05_create_refresh_functions.sql
-- Carga incremental e idempotente da camada analítica.
--
-- analytics.refresh_modelo_analitico():
--   1) insere modelos novos (distintos) em analytics.d_modelo;
--   2) insere processamentos novos em analytics.f_processamentos;
--   3) atualiza fatos existentes cujo conteúdo mudou (comparação por
--      linha via IS DISTINCT FROM), sem apagar/recarregar a fato inteira;
--   4) nunca duplica processamento_id (chave primária + ON CONFLICT);
--   5) registra a execução em analytics.controle_carga;
--   6) funciona normalmente quando não há registros novos (retorna zeros).
-- ============================================================

CREATE OR REPLACE FUNCTION analytics.refresh_modelo_analitico()
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
    -- 1) Modelos distintos encontrados em processamentos.modelo_solicitado
    -- que ainda não existem em d_modelo.
    WITH novos_modelos AS (
        INSERT INTO analytics.d_modelo (modelo_nome, ativo)
        SELECT DISTINCT p.modelo_solicitado, true
        FROM public.processamentos p
        WHERE p.modelo_solicitado IS NOT NULL
        ON CONFLICT (modelo_nome) DO NOTHING
        RETURNING modelo_id
    )
    SELECT COUNT(*)::integer INTO v_dimensoes_inseridas FROM novos_modelos;

    -- 2) e 3) Upsert da fato: um processamento novo é inserido; um
    -- processamento já carregado só é reescrito se algum valor mudou.
    WITH origem_fato AS (
        SELECT
            p.id AS processamento_id,
            to_char(p.criado_em AT TIME ZONE 'UTC', 'YYYYMMDD')::integer AS data_id,
            COALESCE(dm.modelo_id, 0)  AS modelo_id,
            COALESCE(dop.operacao_id, 0) AS operacao_id,
            COALESCE(dor.origem_id, 0) AS origem_id,
            COALESCE(dst.status_id, 0) AS status_id,
            p.criado_em,
            p.encoding_utilizado,
            p.fallback_utilizado,
            p.caracteres,
            p.palavras,
            p.bytes_utf8,
            p.tokens_entrada,
            p.tokens_saida,
            p.total_tokens,
            p.quantidade_blocos,
            p.limite_tokens_bloco,
            p.sobreposicao_tokens,
            p.custo_entrada,
            p.custo_saida,
            p.custo_total,
            p.moeda,
            p.tempo_processamento_ms,
            p.texto_hash,
            p.sucesso,
            (p.mensagem_erro IS NOT NULL) AS possui_erro,
            p.mensagem_erro
        FROM public.processamentos p
        LEFT JOIN analytics.d_modelo   dm  ON dm.modelo_nome = p.modelo_solicitado
        LEFT JOIN analytics.d_operacao dop ON dop.operacao_codigo = p.tipo_operacao
        LEFT JOIN analytics.d_origem   dor ON dor.origem_codigo = p.origem
        LEFT JOIN analytics.d_status   dst ON dst.status_codigo = CASE WHEN p.sucesso THEN 'sucesso' ELSE 'erro' END
    ),
    upsert AS (
        INSERT INTO analytics.f_processamentos AS f (
            processamento_id, data_id, modelo_id, operacao_id, origem_id, status_id,
            criado_em, encoding_utilizado, fallback_utilizado, caracteres, palavras,
            bytes_utf8, tokens_entrada, tokens_saida, total_tokens, quantidade_blocos,
            limite_tokens_bloco, sobreposicao_tokens, custo_entrada, custo_saida,
            custo_total, moeda, tempo_processamento_ms, texto_hash, sucesso,
            possui_erro, mensagem_erro, atualizado_em
        )
        SELECT
            processamento_id, data_id, modelo_id, operacao_id, origem_id, status_id,
            criado_em, encoding_utilizado, fallback_utilizado, caracteres, palavras,
            bytes_utf8, tokens_entrada, tokens_saida, total_tokens, quantidade_blocos,
            limite_tokens_bloco, sobreposicao_tokens, custo_entrada, custo_saida,
            custo_total, moeda, tempo_processamento_ms, texto_hash, sucesso,
            possui_erro, mensagem_erro, now()
        FROM origem_fato
        ON CONFLICT (processamento_id) DO UPDATE SET
            data_id                = EXCLUDED.data_id,
            modelo_id              = EXCLUDED.modelo_id,
            operacao_id            = EXCLUDED.operacao_id,
            origem_id              = EXCLUDED.origem_id,
            status_id              = EXCLUDED.status_id,
            encoding_utilizado     = EXCLUDED.encoding_utilizado,
            fallback_utilizado     = EXCLUDED.fallback_utilizado,
            caracteres             = EXCLUDED.caracteres,
            palavras               = EXCLUDED.palavras,
            bytes_utf8             = EXCLUDED.bytes_utf8,
            tokens_entrada         = EXCLUDED.tokens_entrada,
            tokens_saida           = EXCLUDED.tokens_saida,
            total_tokens           = EXCLUDED.total_tokens,
            quantidade_blocos      = EXCLUDED.quantidade_blocos,
            limite_tokens_bloco    = EXCLUDED.limite_tokens_bloco,
            sobreposicao_tokens    = EXCLUDED.sobreposicao_tokens,
            custo_entrada          = EXCLUDED.custo_entrada,
            custo_saida            = EXCLUDED.custo_saida,
            custo_total            = EXCLUDED.custo_total,
            moeda                  = EXCLUDED.moeda,
            tempo_processamento_ms = EXCLUDED.tempo_processamento_ms,
            texto_hash             = EXCLUDED.texto_hash,
            sucesso                = EXCLUDED.sucesso,
            possui_erro            = EXCLUDED.possui_erro,
            mensagem_erro          = EXCLUDED.mensagem_erro,
            atualizado_em          = now()
        WHERE
            (f.data_id, f.modelo_id, f.operacao_id, f.origem_id, f.status_id,
             f.encoding_utilizado, f.fallback_utilizado, f.caracteres, f.palavras,
             f.bytes_utf8, f.tokens_entrada, f.tokens_saida, f.total_tokens,
             f.quantidade_blocos, f.limite_tokens_bloco, f.sobreposicao_tokens,
             f.custo_entrada, f.custo_saida, f.custo_total, f.moeda,
             f.tempo_processamento_ms, f.texto_hash, f.sucesso, f.possui_erro,
             f.mensagem_erro)
            IS DISTINCT FROM
            (EXCLUDED.data_id, EXCLUDED.modelo_id, EXCLUDED.operacao_id, EXCLUDED.origem_id,
             EXCLUDED.status_id, EXCLUDED.encoding_utilizado, EXCLUDED.fallback_utilizado,
             EXCLUDED.caracteres, EXCLUDED.palavras, EXCLUDED.bytes_utf8,
             EXCLUDED.tokens_entrada, EXCLUDED.tokens_saida, EXCLUDED.total_tokens,
             EXCLUDED.quantidade_blocos, EXCLUDED.limite_tokens_bloco,
             EXCLUDED.sobreposicao_tokens, EXCLUDED.custo_entrada, EXCLUDED.custo_saida,
             EXCLUDED.custo_total, EXCLUDED.moeda, EXCLUDED.tempo_processamento_ms,
             EXCLUDED.texto_hash, EXCLUDED.sucesso, EXCLUDED.possui_erro,
             EXCLUDED.mensagem_erro)
        RETURNING (xmax = 0) AS foi_inserido
    )
    SELECT
        COALESCE(COUNT(*) FILTER (WHERE foi_inserido), 0)::integer,
        COALESCE(COUNT(*) FILTER (WHERE NOT foi_inserido), 0)::integer
    INTO v_fatos_inseridos, v_fatos_atualizados
    FROM upsert;

    v_mensagem := format(
        'Refresh concluído: %s modelo(s) novo(s) em d_modelo, %s fato(s) inserido(s), %s fato(s) atualizado(s).',
        v_dimensoes_inseridas, v_fatos_inseridos, v_fatos_atualizados
    );

    INSERT INTO analytics.controle_carga (
        processo, iniciado_em, finalizado_em, status,
        registros_inseridos, registros_atualizados, mensagem
    ) VALUES (
        'refresh_modelo_analitico', v_inicio, clock_timestamp(), 'sucesso',
        v_dimensoes_inseridas + v_fatos_inseridos, v_fatos_atualizados, v_mensagem
    );

    RETURN QUERY
    SELECT v_dimensoes_inseridas, v_fatos_inseridos, v_fatos_atualizados, clock_timestamp();
END;
$$;

COMMENT ON FUNCTION analytics.refresh_modelo_analitico() IS
    'Carga incremental e idempotente de analytics.d_modelo e '
    'analytics.f_processamentos a partir de public.processamentos. '
    'Não apaga nem recria a fato; usa INSERT ... ON CONFLICT.';
