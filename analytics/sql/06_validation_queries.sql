-- ============================================================
-- 06_validation_queries.sql
-- Consultas manuais de validação da camada analítica.
-- Não são executadas pela migração — rode manualmente via psql ou
-- qualquer cliente PostgreSQL após `uv run alembic upgrade head` e
-- `uv run python scripts/refresh_analytics.py`.
-- ============================================================

-- Volume das dimensões
SELECT COUNT(*) AS linhas_d_calendario FROM analytics.d_calendario;
SELECT COUNT(*) AS linhas_d_modelo    FROM analytics.d_modelo;
SELECT COUNT(*) AS linhas_d_operacao  FROM analytics.d_operacao;
SELECT COUNT(*) AS linhas_d_origem    FROM analytics.d_origem;
SELECT COUNT(*) AS linhas_d_status    FROM analytics.d_status;

-- Volume da fato e comparação com a tabela operacional
SELECT COUNT(*) AS linhas_f_processamentos FROM analytics.f_processamentos;
SELECT COUNT(*) AS linhas_processamentos   FROM public.processamentos;

-- As duas contagens acima devem ser iguais após um refresh completo.

-- Chaves especiais (id = 0) presentes em cada dimensão
SELECT * FROM analytics.d_modelo   WHERE modelo_id = 0;
SELECT * FROM analytics.d_operacao WHERE operacao_id = 0;
SELECT * FROM analytics.d_origem   WHERE origem_id = 0;
SELECT * FROM analytics.d_status   WHERE status_id = 0;

-- Nenhum processamento_id duplicado na fato
SELECT processamento_id, COUNT(*)
FROM analytics.f_processamentos
GROUP BY processamento_id
HAVING COUNT(*) > 1;

-- Histórico de cargas (mais recentes primeiro)
SELECT * FROM analytics.controle_carga ORDER BY iniciado_em DESC LIMIT 5;

-- Amostras das views de consumo
SELECT * FROM analytics.vw_powerbi_processamentos    LIMIT 10;
SELECT * FROM analytics.vw_powerbi_resumo_diario      LIMIT 10;
SELECT * FROM analytics.vw_powerbi_resumo_mensal      LIMIT 10;
SELECT * FROM analytics.vw_powerbi_textos_repetidos   LIMIT 10;

-- Ordenação correta da dimensão calendário
SELECT data_id, ano_mes, numero_mes, nome_mes
FROM analytics.d_calendario
ORDER BY ano_mes_numero
LIMIT 15;
