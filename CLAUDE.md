# Token Intelligence Platform

## Objetivo

Desenvolver uma plataforma local para análise e governança de tokens de aplicações com modelos de linguagem.

A plataforma deverá conter:

- contador de tokens;
- estimador de custos;
- divisor de documentos por quantidade de tokens;
- auditor de prompts;
- API FastAPI;
- armazenamento futuro em PostgreSQL;
- integração futura com Power BI;
- Docker;
- testes automatizados.

## Tecnologias

- Python 3.12 ou superior
- uv para dependências e execução
- tiktoken para tokenização
- FastAPI para API
- Pydantic para validação
- Pytest para testes
- PostgreSQL em fase posterior
- Docker em fase posterior

## Regras

- Use sempre type hints.
- Use funções pequenas e bem definidas.
- Não coloque toda a lógica em main.py.
- Separe regras de negócio, schemas e rotas.
- Não exponha token_ids por padrão.
- Não altere arquivos sem antes explicar o que será feito.
- Execute os testes após cada alteração relevante.
- Não implemente PostgreSQL, Docker ou Power BI nesta primeira fase.
- Use português do Brasil nos textos de interface e documentação.

## Comandos do projeto

Instalar dependências:

uv sync

Executar:

uv run python main.py

Executar testes:

uv run pytest

## Primeira fase

Implementar somente:

1. análise de texto;
2. contagem de tokens;
3. quantidade de caracteres;
4. quantidade de palavras;
5. tamanho em bytes;
6. média de caracteres por token;
7. tempo de processamento;
8. testes automatizados.

## Segunda fase (concluída)

Implementado, mantendo compatibilidade com Windows, Git Bash, Python 3.13 e uv:

1. estimador configurável de custos (`app/services/cost_estimator.py`), com preços em
   `app/config/model_prices.json` (valores demonstrativos, usando `Decimal`);
2. divisor de textos por tokens (`app/core/splitter.py`), com sobreposição opcional;
3. comparador de tokenização entre modelos (`app/services/model_comparator.py`), com
   indicação explícita de fallback para `o200k_base`;
4. menu interativo no terminal (`app/cli/menu.py`), com `main.py` apenas iniciando o menu;
5. testes automatizados para cada módulo novo.

Estrutura real do projeto após a segunda fase:

```
app/
├── core/ (tokenizer.py, splitter.py)
├── services/ (cost_estimator.py, model_comparator.py)
├── config/ (model_prices.json)
└── cli/ (menu.py)
```

Continuam fora de escopo: PostgreSQL, Docker, Power BI, tradução automática, compressão
semântica e chamadas externas de IA.

## Terceira fase (concluída)

Implementada uma API FastAPI local que reutiliza integralmente as regras de negócio das
fases anteriores (`app/core` e `app/services`), sem duplicar lógica. O menu CLI
(`app/cli/menu.py`) e o `main.py` (que continua iniciando apenas o menu) foram
preservados sem alterações de comportamento.

### Arquitetura da API

```
app/
├── api/
│   ├── app.py              # instância FastAPI, rota raiz e tratamento de erros
│   ├── dependencies.py      # dependências compartilhadas entre rotas (ex.: caminho de preços)
│   └── routes/
│       ├── health.py        # GET /health
│       ├── tokens.py        # POST /api/v1/tokens/analisar
│       ├── splitter.py      # POST /api/v1/tokens/dividir
│       ├── comparator.py    # POST /api/v1/tokens/comparar-modelos
│       └── costs.py         # POST /api/v1/custos/estimar
└── schemas/
    ├── token_schemas.py
    ├── splitter_schemas.py
    ├── comparator_schemas.py
    └── cost_schemas.py
```

### Comandos da API

Executar a API (não sobe automaticamente com `main.py`):

```bash
uv run uvicorn app.api.app:app --reload
```

Endereços locais: API em `http://127.0.0.1:8000`, Swagger em `/docs`, ReDoc em `/redoc`.

### Endpoints implementados

- `GET /` — informações gerais da API.
- `GET /health` — verificação de saúde.
- `POST /api/v1/tokens/analisar` — reutiliza `app/core/tokenizer.py`.
- `POST /api/v1/tokens/dividir` — reutiliza `app/core/splitter.py`.
- `POST /api/v1/tokens/comparar-modelos` — reutiliza `app/services/model_comparator.py`.
- `POST /api/v1/custos/estimar` — reutiliza `app/services/cost_estimator.py`.

Erros de regra de negócio (`ValueError`) são convertidos em HTTP 422 com mensagem clara
em português; erros inesperados retornam HTTP 500 sem expor stack trace.

## Quarta fase (concluída)

Adicionado o histórico de processamentos em PostgreSQL, preservando integralmente o menu
CLI, a API e todos os endpoints/serviços das fases anteriores.

### Nova camada de banco

```
app/
├── database/ (base.py, session.py, models/processamento.py)
├── repositories/ (processamento_repository.py)
├── services/processing_history.py
└── config/settings.py  # pydantic-settings, lê DATABASE_URL/.env
```

- SQLAlchemy 2 (`DeclarativeBase`, `Mapped`, `mapped_column`) com `psycopg` v3.
- Tabela `processamentos` guarda métricas e metadados de cada operação (nunca o texto
  completo nem `token_ids`); apenas `texto_hash` (SHA-256) e `texto_preview` (200
  caracteres) são persistidos. `SALVAR_TEXTO_COMPLETO` fica `false` por padrão.

### Repository pattern

`ProcessamentoRepository` (`app/repositories/processamento_repository.py`) concentra
todo o acesso a dados (`criar`, `buscar_por_id`, `listar`, `contar`, `listar_por_tipo`,
`listar_por_periodo`, `obter_resumo`), sem regra de negócio.

### Serviço de histórico

`app/services/processing_history.py` transforma resultados das operações em registros
do banco (`registrar_analise`, `registrar_divisao`, `registrar_comparacao`,
`registrar_estimativa_custo`, `registrar_erro`). Falhas de persistência são registradas
em log e nunca derrubam a resposta principal da API.

### Comandos Alembic

```bash
uv run alembic upgrade head
uv run alembic current
uv run alembic history
```

A URL de conexão vem sempre de `app/config/settings.py` (variável `DATABASE_URL` /
arquivo `.env`), nunca de `alembic.ini`.

### Novos endpoints

- `GET /api/v1/historico` — lista paginada, com filtros por tipo, modelo, sucesso e
  período.
- `GET /api/v1/historico/{processamento_id}` — busca por ID (404 se inexistente).
- `GET /api/v1/historico/resumo` — métricas agregadas do histórico.

## Quinta fase (concluída)

Adicionada uma stack Docker Compose reproduzível, independente de qualquer container
externo, preservando integralmente o menu CLI, a API, o Swagger, o banco/modelos
SQLAlchemy, as migrações Alembic, os endpoints de histórico, os testes e as
funcionalidades de análise, divisão, comparação e custos das fases anteriores.

### Arquivos novos

```
Dockerfile              # imagem da API (Python 3.13-slim, uv, usuário não root)
docker-entrypoint.sh    # aguarda o PostgreSQL, roda alembic upgrade head, inicia a API
compose.yaml            # serviços postgres + api, rede e volume próprios
.dockerignore
.env.docker.example     # modelo de variáveis (sem senha real)
```

### Serviços e nomes

- `postgres` → container `token-intelligence-postgres`, imagem `postgres:16.4`.
- `api` → container `token-intelligence-api`, construída pelo `Dockerfile` local.
- Rede: `token-intelligence-network`. Volume: `token_intelligence_postgres_data`.

Totalmente isolada dos containers externos `my-postgres` (5433) e `my-pgadmin`
(15432), que não são usados, alterados nem referenciados por esta stack.

### Portas

- PostgreSQL: host `5434` → container `5432`.
- API: host `8000` → container `8000`.
- Dentro da stack, a API sempre se conecta via `postgres:5432` (nunca `localhost`).

### Comandos Docker

```bash
cp .env.docker.example .env.docker   # ajustar a senha antes de usar
docker compose --env-file .env.docker up --build -d
docker compose --env-file .env.docker ps
docker compose --env-file .env.docker logs -f api
docker compose --env-file .env.docker down       # mantém o volume
docker compose --env-file .env.docker down -v    # remove o volume (dados perdidos)
```

`app/config/settings.py` e `alembic/env.py` não precisaram de alterações: ambos já
liam a URL do banco exclusivamente de variáveis de ambiente, o que permitiu que a
mesma configuração funcionasse local e dentro do container apenas trocando
`DATABASE_URL` no `.env` (local) ou no `compose.yaml` (Docker).

## Sexta fase (concluída)

Adicionado o modelo analítico para Power BI (schema `analytics`), preservando
integralmente o menu CLI, a API, o Swagger, o PostgreSQL, a tabela `processamentos`,
o SQLAlchemy, o Alembic, os endpoints de histórico, o Docker Compose e os testes das
fases anteriores. A camada analítica é derivada de `processamentos` e nunca a altera.

### Camada `analytics` e modelo estrela

```
analytics/
├── README.md
├── sql/
│   ├── 01_create_schema.sql            # CREATE SCHEMA analytics
│   ├── 02_create_dimensions.sql        # d_calendario, d_modelo, d_operacao, d_origem, d_status
│   ├── 03_create_fact.sql              # f_processamentos + controle_carga + índices
│   ├── 04_create_views.sql             # views vw_powerbi_*
│   ├── 05_create_refresh_functions.sql # analytics.refresh_modelo_analitico()
│   ├── 06_validation_queries.sql       # consultas manuais (não executadas pela migração)
│   └── 07_powerbi_source_queries.sql   # consultas prontas para o Power BI
├── dax/           # medidas_base, medidas_tokens, medidas_custos, medidas_desempenho, medidas_qualidade
├── docs/          # modelo_estrela, dicionario_dados, indicadores_powerbi, guia_conexao_powerbi
└── diagrams/modelo_estrela.mmd
```

Modelo estrela: dimensões `d_calendario` (2024-01-01 a 2035-12-31, pt-BR),
`d_modelo`, `d_operacao`, `d_origem`, `d_status` (todas com chave especial `id = 0`
"Não informado") e a fato `f_processamentos` (grão: uma linha por registro de
`processamentos`, sem `texto_preview` nem `metadados`, nunca `token_ids`).
Relacionamentos sempre `dimensão 1:* fato`, direção única. Detalhes completos em
`analytics/docs/modelo_estrela.md` e `analytics/docs/dicionario_dados.md`.

### Migração Alembic dedicada

`alembic/versions/d93bc6ab6522_criar_camada_analytics.py` lê e executa
`analytics/sql/01` a `05` (fonte única de verdade, sem duplicar SQL). O `downgrade()`
executa apenas `DROP SCHEMA analytics CASCADE` — nunca toca `processamentos`. Não usa
`Base.metadata.create_all` como mecanismo principal.

### Refresh (carga incremental e idempotente)

`analytics.refresh_modelo_analitico()` insere modelos novos em `d_modelo`, faz
upsert (`INSERT ... ON CONFLICT`) em `f_processamentos` e registra cada execução em
`analytics.controle_carga`. Nunca trunca/recarrega a fato inteira.

```bash
uv run python scripts/refresh_analytics.py
```

### Endpoints administrativos

- `POST /api/v1/analytics/atualizar` — executa o refresh; ainda sem autenticação
  nesta fase (documentar necessidade de proteção antes de produção).
- `GET /api/v1/analytics/status` — última execução registrada em `controle_carga`.

### Novos arquivos de código

```
app/repositories/analytics_repository.py  # executa o refresh e lê controle_carga
app/schemas/analytics_schemas.py
app/api/routes/analytics.py
scripts/refresh_analytics.py
```

Ainda não implementados: auditor de prompts, compactador de prompts, tradução
automática, compressão semântica e chamadas externas de IA (Fase 7, pendente).

## Sétima fase (concluída)

Adicionados o auditor e o compactador local de prompts (regras locais, sem IA
externa), preservando integralmente o menu CLI, a API, o Swagger, o
PostgreSQL, o histórico de processamentos, a camada analytics, o modelo
analítico para Power BI, o Docker Compose, o Alembic, os testes e as
funcionalidades de análise, divisão, comparação e custos das fases
anteriores. Nunca chama OpenAI, Anthropic, Claude ou qualquer IA externa; não
há tradução, embeddings, banco vetorial ou processamento semântico por LLM.

### Princípio fundamental

O compactador não promete preservação perfeita de significado. O texto
compactado é sempre uma sugestão: a API/CLI nunca substituem o texto original
automaticamente — a aprovação é sempre um passo humano explícito
(`POST /api/v1/prompts/aprovar`).

### Novos módulos

```
app/
├── core/
│   ├── protected_terms.py    # protege números, datas, %, R$, URLs, identificadores,
│   │                         # blocos de código, MAIÚSCULAS e termos técnicos
│   │                         # configurados, via marcadores opacos (\x00...\x00)
│   └── text_normalizer.py    # regras conservadoras (espaços, pontuação, duplicidades)
├── services/
│   ├── prompt_auditor.py           # auditar_prompt(): diagnóstico sem alterar o texto
│   ├── prompt_compressor.py        # compactar_prompt(): 3 níveis (conservador/
│   │                                # moderado/agressivo), nunca aplica automaticamente
│   └── compression_comparator.py   # comparar_niveis(): ranking + recomendação por risco
├── config/
│   ├── compression_rules.json      # substituições/remoções configuráveis por nível
│   └── protected_terms.json        # termos técnicos protegidos, editável sem código
├── schemas/
│   └── compression_schemas.py
├── database/models/
│   └── compactacao_prompt.py       # modelo da tabela compactacoes_prompt
├── repositories/
│   └── compactacao_prompt_repository.py
└── api/routes/
    └── compression.py              # POST /api/v1/prompts/*
```

### Níveis de compactação e riscos

- **Conservador** (risco baixo): espaços duplicados, linhas vazias
  excessivas, pontuação repetida, palavras consecutivas duplicadas, espaços
  antes/depois de pontuação e parênteses, saudações isoladas simples.
- **Moderado** (risco médio): inclui o conservador + simplificação de
  expressões redundantes configuradas em `app/config/compression_rules.json`
  (ex.: "gostaria que você pudesse" → removido).
- **Agressivo** (risco alto): inclui o moderado + remoções mais amplas
  (introduções/conclusões redundantes). Sempre exibe aviso de risco alto e
  nunca é aplicado automaticamente.

Se o texto compactado não reduzir a quantidade de tokens, o texto original é
mantido e `compactacao_aplicada` retorna `false`.

### Preservação de termos essenciais

`app/core/protected_terms.py` protege, antes de qualquer regra ser aplicada:
números, datas (`2026-07-19`), percentuais, valores monetários (`R$
1.500,00`), URLs, caminhos de arquivo, host:porta (`localhost:5433`), nomes
entre aspas, blocos de código, identificadores com underscore ou ponto
(`analytics.f_processamentos`, `BITS_COUNT`), identificadores camelCase
(`fConsumoConsolidado`), palavras totalmente em maiúsculas e termos técnicos
configurados em `app/config/protected_terms.json` (mais os informados em
`termos_protegidos` na requisição/CLI). Esses trechos nunca são alterados,
independentemente do nível de compactação.

### Novos endpoints

- `POST /api/v1/prompts/auditar` — reutiliza `app/services/prompt_auditor.py`.
- `POST /api/v1/prompts/compactar` — reutiliza `app/services/prompt_compressor.py`;
  retorna `compactacao_id` para aprovação posterior.
- `POST /api/v1/prompts/comparar-compactacao` — reutiliza
  `app/services/compression_comparator.py`.
- `POST /api/v1/prompts/aprovar` — registra a aprovação humana de uma
  compactação já gerada (não executa nenhuma chamada externa).
- `POST /api/v1/analytics/atualizar-compactacoes` e
  `GET /api/v1/analytics/status-compactacoes` — carga incremental da fato de
  compactações, em função separada de `refresh_modelo_analitico()` (não
  altera sua assinatura nem seu comportamento).

### Novas tabelas

`compactacoes_prompt` (migração `e7f1c9a2b4d6`): guarda métricas, hash SHA-256
e preview de 200 caracteres do texto original e do compactado — nunca o texto
completo, nunca `token_ids`. Novos tipos de operação em `processamentos`:
`auditoria_prompt`, `compactacao_prompt`, `comparacao_compactacao`.

### Camada analytics

Migração `f3a8d2c6b1e9` (lê `analytics/sql/08..11`) adiciona a dimensão
`analytics.d_nivel_compactacao`, a fato `analytics.f_compactacoes_prompt`, as
views `vw_powerbi_compactacoes`, `vw_powerbi_resumo_compactacao_diario` e
`vw_powerbi_resumo_compactacao_mensal`, e a função
`analytics.refresh_compactacoes_prompt()` — separada de
`refresh_modelo_analitico()`, para não alterar o refresh já existente.
Medidas DAX em `analytics/dax/medidas_compactacao.dax`.

### CLI

Menu atualizado: 1-4 inalteradas; 5. Auditar prompt; 6. Compactar prompt;
7. Comparar níveis de compactação; 8. Sair. A compactação sempre pergunta se
o usuário aprova o resultado antes de encerrar a operação, sem jamais
sobrescrever o texto original automaticamente.