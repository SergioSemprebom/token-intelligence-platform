# Camada analítica (Fase 6) — Modelo para Power BI

Modelo estrela em PostgreSQL, no schema `analytics`, derivado da tabela
operacional `public.processamentos`, preparado para conexão direta com o
Power BI. Não altera, nem depende de escrita em, `processamentos`.

## Estrutura

```
analytics/
├── sql/
│   ├── 01_create_schema.sql            # CREATE SCHEMA analytics
│   ├── 02_create_dimensions.sql        # d_calendario, d_modelo, d_operacao, d_origem, d_status
│   ├── 03_create_fact.sql              # f_processamentos + controle_carga + índices
│   ├── 04_create_views.sql             # views vw_powerbi_*
│   ├── 05_create_refresh_functions.sql # analytics.refresh_modelo_analitico()
│   ├── 06_validation_queries.sql       # consultas manuais de validação
│   └── 07_powerbi_source_queries.sql   # consultas prontas para "Consulta SQL" no Power BI
├── dax/                                # medidas DAX (ver abaixo)
├── docs/
│   ├── modelo_estrela.md
│   ├── dicionario_dados.md
│   ├── indicadores_powerbi.md
│   └── guia_conexao_powerbi.md
└── diagrams/
    └── modelo_estrela.mmd
```

Os arquivos em `sql/01` a `sql/05` são a fonte única de verdade do DDL: a
migração Alembic (`alembic/versions/<rev>_criar_camada_analytics.py`) apenas
lê e executa esses arquivos — nada é duplicado entre o SQL solto e a migração.
`06` e `07` são apenas para uso manual (psql / Power BI), não são executados
pela migração.

## Como aplicar

```bash
uv run alembic upgrade head
uv run python scripts/refresh_analytics.py
```

## Documentação

- Modelo estrela e relacionamentos: [`docs/modelo_estrela.md`](docs/modelo_estrela.md)
- Dicionário de dados completo: [`docs/dicionario_dados.md`](docs/dicionario_dados.md)
- Indicadores e páginas sugeridas do relatório: [`docs/indicadores_powerbi.md`](docs/indicadores_powerbi.md)
- Conexão do Power BI (Power Query M, sem credenciais no código): [`docs/guia_conexao_powerbi.md`](docs/guia_conexao_powerbi.md)

## Medidas DAX

Arquivos `.dax` em `dax/`, agrupados por tema: `medidas_base`, `medidas_tokens`,
`medidas_custos`, `medidas_desempenho`, `medidas_qualidade`. Use os nomes de
tabela `fProcessamentos`, `dCalendario`, `dModelo`, `dOperacao`, `dOrigem`,
`dStatus` ao renomear as tabelas importadas no Power BI.

## Endpoints administrativos

- `POST /api/v1/analytics/atualizar` — executa `analytics.refresh_modelo_analitico()`.
- `GET /api/v1/analytics/status` — retorna a última execução registrada em `analytics.controle_carga`.

Consulte o `CLAUDE.md` na raiz do projeto (seção "Sexta fase" / analytics) para
o status geral do projeto e limitações atuais.
