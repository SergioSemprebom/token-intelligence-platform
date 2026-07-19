-- ============================================================
-- 01_create_schema.sql
-- Schema da camada analítica (Fase 6 — modelo para Power BI)
--
-- A camada analítica é completamente separada da tabela
-- operacional `processamentos`: nenhum objeto deste schema altera,
-- referencia em escrita ou apaga dados da tabela operacional.
-- ============================================================

CREATE SCHEMA IF NOT EXISTS analytics;

COMMENT ON SCHEMA analytics IS
    'Camada analítica (modelo estrela) preparada para consumo pelo Power BI. '
    'Somente leitura derivada da tabela operacional public.processamentos.';
