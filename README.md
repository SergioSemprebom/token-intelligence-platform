# Token Intelligence Platform

Plataforma local para análise e governança de tokens de aplicações com modelos de linguagem.

## Objetivo

Fornecer, em um único lugar, ferramentas para contar tokens, estimar custos, dividir documentos por
tokens e comparar o comportamento de tokenização entre diferentes modelos, com histórico de
processamentos persistido em PostgreSQL, evoluindo futuramente para integração com Power BI e
distribuição via Docker.

## Funcionalidades atuais

### Primeira fase

- Análise de texto: contagem de tokens, caracteres, palavras, bytes UTF-8, média de caracteres por
  token e tempo de processamento.
- Ocultação de `token_ids` por padrão, com exibição opcional.

### Segunda fase

- **Estimador de custos** configurável, com preços por modelo carregados de um arquivo JSON externo
  (`app/config/model_prices.json`), sem necessidade de alterar código para atualizar valores.
- **Divisor de textos por tokens**, com suporte a sobreposição entre blocos, respeitando sempre a
  contagem real de tokens do modelo (nunca por quantidade de caracteres).
- **Comparador de tokenização entre modelos**, informando explicitamente quando um modelo desconhecido
  utiliza fallback para a codificação `o200k_base`.
- **Menu interativo no terminal**, com tratamento de erros por opção (uma falha não interrompe a
  aplicação) e retorno automático ao menu principal após cada operação.

### Terceira fase

- **API FastAPI local**, com documentação automática em Swagger e ReDoc, reutilizando as
  mesmas regras de negócio do menu interativo (nenhuma lógica foi duplicada).
- Endpoints para análise de texto, divisão por tokens, comparação entre modelos e
  estimativa de custos, além de rota raiz e rota de saúde.
- Tratamento consistente de erros: violações de regra de negócio retornam HTTP 422 com
  mensagem clara em português, e erros inesperados nunca expõem stack trace ao cliente.

### Quarta fase

- **Histórico de processamentos em PostgreSQL**: cada operação bem-sucedida da API
  (análise, divisão, comparação e estimativa de custo) é registrada na tabela
  `processamentos`, com métricas e metadados para futura alimentação de um dashboard
  Power BI.
- **SQLAlchemy 2** (`Mapped`/`mapped_column`) com fábrica de sessão dedicada e
  **Alembic** para migrações versionadas — sem uso de `create_all` em produção.
- **Repository pattern** (`ProcessamentoRepository`) isolando todo o acesso a dados, e
  um **serviço de histórico** (`processing_history.py`) responsável por transformar
  resultados das operações em registros do banco.
- **Privacidade por padrão**: o texto completo processado nunca é armazenado. Apenas o
  SHA-256 (`texto_hash`) e os primeiros 200 caracteres (`texto_preview`) são persistidos.
- **Resiliência**: se o PostgreSQL estiver indisponível, a operação principal da API
  continua respondendo normalmente — a falha de persistência do histórico é apenas
  registrada em log, nunca esconde o problema nem derruba a resposta ao cliente.
- Novos endpoints `GET /api/v1/historico`, `GET /api/v1/historico/{id}` e
  `GET /api/v1/historico/resumo`.

### Quinta fase

- **Docker Compose** reproduzível (API + PostgreSQL), independente de qualquer
  container externo (ver [Docker Compose (Fase 5)](#docker-compose-fase-5)).

### Sexta fase

- **Camada analítica para Power BI** (`schema analytics`), modelo estrela derivado da
  tabela operacional `processamentos`, sem alterá-la (ver
  [Camada analítica (Fase 6)](#camada-analítica-fase-6)).
- Carga incremental e idempotente via `analytics.refresh_modelo_analitico()`, executável
  por `scripts/refresh_analytics.py` ou pelo endpoint administrativo
  `POST /api/v1/analytics/atualizar`.
- Views `vw_powerbi_*`, medidas DAX e documentação de conexão em `analytics/`.

### Sétima fase

- **Auditor e compactador local de prompts** (regras locais, sem tradução e sem
  nenhuma chamada de IA externa), com três níveis de risco crescente (ver
  [Auditor e compactador de prompts (Fase 7)](#auditor-e-compactador-de-prompts-fase-7)).
- **Proteção de termos essenciais** (números, datas, valores monetários, identificadores
  técnicos, URLs, blocos de código etc.) contra qualquer alteração do compactador.
- **Aprovação humana obrigatória**: o texto compactado é sempre uma sugestão — nunca
  substitui o original automaticamente.
- Novos endpoints `POST /api/v1/prompts/auditar`, `/compactar`, `/comparar-compactacao`
  e `/aprovar`, nova tabela `compactacoes_prompt` e extensão da camada analytics
  (`f_compactacoes_prompt`, `d_nivel_compactacao`, views e medidas DAX dedicadas).

## Estrutura do projeto

```
app/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── tokenizer.py       # análise de texto e obtenção de encoding (com detecção de fallback)
│   ├── splitter.py        # divisão de textos por quantidade de tokens
│   ├── protected_terms.py # protege números, datas, identificadores etc. (Fase 7)
│   └── text_normalizer.py # regras conservadoras de compactação (Fase 7)
├── services/
│   ├── __init__.py
│   ├── cost_estimator.py       # estimativa de custos com Decimal, a partir do JSON de preços
│   ├── model_comparator.py     # comparação de tokenização entre modelos
│   ├── processing_history.py   # transforma resultados das operações em histórico
│   ├── prompt_auditor.py       # auditar_prompt(): diagnóstico de desperdícios (Fase 7)
│   ├── prompt_compressor.py    # compactar_prompt(): 3 níveis de compactação (Fase 7)
│   └── compression_comparator.py  # comparar_niveis(): ranking + recomendação (Fase 7)
├── config/
│   ├── __init__.py
│   ├── settings.py        # configurações via pydantic-settings (.env)
│   ├── model_prices.json  # preços demonstrativos por modelo (editável sem alterar código)
│   ├── compression_rules.json  # regras de compactação por nível (Fase 7)
│   └── protected_terms.json    # termos técnicos protegidos (Fase 7)
├── database/
│   ├── __init__.py
│   ├── base.py             # DeclarativeBase do SQLAlchemy 2
│   ├── session.py          # engine e fábrica de sessão
│   └── models/
│       ├── __init__.py
│       ├── processamento.py       # modelo da tabela `processamentos`
│       └── compactacao_prompt.py  # modelo da tabela `compactacoes_prompt` (Fase 7)
├── repositories/
│   ├── __init__.py
│   ├── processamento_repository.py       # acesso a dados do histórico (sem regra de negócio)
│   ├── analytics_repository.py           # executa o refresh e lê analytics.controle_carga
│   └── compactacao_prompt_repository.py  # acesso a dados de compactacoes_prompt (Fase 7)
├── cli/
│   ├── __init__.py
│   └── menu.py            # menu interativo do terminal
├── api/
│   ├── __init__.py
│   ├── app.py              # instância FastAPI, rota raiz e tratamento de erros
│   ├── dependencies.py      # dependências compartilhadas entre rotas
│   └── routes/
│       ├── __init__.py
│       ├── health.py        # GET /health
│       ├── tokens.py        # POST /api/v1/tokens/analisar
│       ├── splitter.py      # POST /api/v1/tokens/dividir
│       ├── comparator.py    # POST /api/v1/tokens/comparar-modelos
│       ├── costs.py         # POST /api/v1/custos/estimar
│       ├── historico.py     # GET /api/v1/historico e derivados
│       ├── analytics.py     # POST/GET /api/v1/analytics/* (carga da camada Power BI)
│       └── compression.py   # POST /api/v1/prompts/* (auditor/compactador, Fase 7)
└── schemas/
    ├── __init__.py
    ├── token_schemas.py
    ├── splitter_schemas.py
    ├── comparator_schemas.py
    ├── cost_schemas.py
    ├── historico_schemas.py
    ├── analytics_schemas.py
    └── compression_schemas.py

alembic/
├── env.py                 # lê DATABASE_URL de app/config/settings.py
├── script.py.mako
└── versions/
    ├── d4f1a1c9b2e3_criar_tabela_processamentos.py
    ├── d93bc6ab6522_criar_camada_analytics.py         # lê e executa analytics/sql/01..05
    ├── e7f1c9a2b4d6_criar_tabela_compactacoes_prompt.py
    └── f3a8d2c6b1e9_criar_camada_analytics_compactacao.py  # lê e executa analytics/sql/08..11

analytics/                 # camada analítica (Fases 6 e 7) — ver seções dedicadas abaixo
├── README.md
├── sql/          # 01_create_schema .. 07_powerbi_source_queries (Fase 6)
│                 # 08_create_compression_dimension .. 11_create_compression_refresh (Fase 7)
├── dax/          # medidas_base, medidas_tokens, medidas_custos, medidas_desempenho,
│                 # medidas_qualidade, medidas_compactacao (Fase 7)
├── docs/         # modelo_estrela, dicionario_dados, indicadores_powerbi, guia_conexao_powerbi
└── diagrams/
    └── modelo_estrela.mmd

scripts/
└── refresh_analytics.py   # `uv run python scripts/refresh_analytics.py` (processamentos + compactações)

tests/
├── test_tokenizer.py
├── test_splitter.py
├── test_cost_estimator.py
├── test_model_comparator.py
├── test_text_normalizer.py         # Fase 7
├── test_prompt_auditor.py          # Fase 7
├── test_prompt_compressor.py       # Fase 7
├── test_compression_comparator.py  # Fase 7
├── test_menu.py
├── test_main.py
├── test_settings.py
├── test_refresh_analytics_script.py  # unitário: formatação do servidor sem credenciais
├── conftest.py             # SQLite em memória isolado por teste (sem PostgreSQL real)
├── database/
│   └── test_processamento_repository.py
├── services/
│   └── test_processing_history.py
├── integration/
│   ├── test_postgres_integration.py    # marcados com @pytest.mark.integration
│   └── test_analytics_integration.py   # idem — exige `alembic upgrade head` aplicado
└── api/
    ├── test_health_api.py
    ├── test_tokens_api.py
    ├── test_splitter_api.py
    ├── test_comparator_api.py
    ├── test_costs_api.py
    ├── test_historico_api.py
    ├── test_analytics_api.py
    └── test_compression_api.py    # Fase 7

alembic.ini
main.py                    # apenas inicia o menu interativo (não inicia a API)
.env.example                # modelo de variáveis de ambiente (sem senha real)
Dockerfile                  # imagem da API (Fase 5)
docker-entrypoint.sh        # aguarda o PostgreSQL e aplica migrações no container
compose.yaml                # stack Docker (API + PostgreSQL), independente de terceiros
.dockerignore
.env.docker.example         # modelo de variáveis da stack Docker (sem senha real)
```

## Instalação

Requer Python 3.12 ou superior (testado com Python 3.13) e [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

## Execução

```bash
uv run python main.py
```

O menu interativo apresenta as opções:

```
1. Analisar texto
2. Estimar custo
3. Dividir texto por tokens
4. Comparar modelos
5. Auditar prompt
6. Compactar prompt
7. Comparar níveis de compactação
8. Sair
```

Textos com várias linhas devem ser finalizados com uma linha contendo apenas `FIM`. Nas
opções 6 e 7, o texto original nunca é sobrescrito automaticamente — a compactação (opção
6) sempre pergunta se você aprova o resultado antes de encerrar.

## Execução da API

A API é executada separadamente do menu CLI (o `main.py` continua iniciando apenas o menu):

```bash
uv run uvicorn app.api.app:app --reload
```

Endereços locais:

- API: http://127.0.0.1:8000
- Swagger: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc
- OpenAPI JSON: http://127.0.0.1:8000/openapi.json

### Endpoints disponíveis

| Método | Rota | Descrição |
| --- | --- | --- |
| GET | `/` | Informações gerais da API |
| GET | `/health` | Verificação de saúde da aplicação |
| POST | `/api/v1/tokens/analisar` | Analisa um texto e retorna métricas de tokenização |
| POST | `/api/v1/tokens/dividir` | Divide um texto em blocos por quantidade de tokens |
| POST | `/api/v1/tokens/comparar-modelos` | Compara a tokenização de um texto entre modelos |
| POST | `/api/v1/custos/estimar` | Estima o custo de uso de tokens para um modelo |
| GET | `/api/v1/historico` | Lista o histórico de processamentos, paginado e filtrável |
| GET | `/api/v1/historico/{id}` | Busca um processamento específico pelo identificador |
| GET | `/api/v1/historico/resumo` | Métricas agregadas do histórico de processamentos |
| POST | `/api/v1/analytics/atualizar` | Executa a carga incremental da camada analítica (Power BI) |
| GET | `/api/v1/analytics/status` | Última execução registrada em `analytics.controle_carga` |
| POST | `/api/v1/prompts/auditar` | Audita um prompt e identifica desperdícios, sem alterá-lo |
| POST | `/api/v1/prompts/compactar` | Compacta um prompt localmente (sugestão, não substitui automaticamente) |
| POST | `/api/v1/prompts/comparar-compactacao` | Compara os três níveis de compactação para o mesmo texto |
| POST | `/api/v1/prompts/aprovar` | Registra a aprovação humana de uma compactação já gerada |
| POST | `/api/v1/analytics/atualizar-compactacoes` | Carga incremental da fato de compactações de prompt (Power BI) |
| GET | `/api/v1/analytics/status-compactacoes` | Última execução do refresh de compactações |

Cada chamada bem-sucedida às quatro primeiras rotas grava automaticamente um registro no
histórico (ver seção [Configuração do PostgreSQL](#configuração-do-postgresql-fase-4)). O
mesmo vale para as rotas de auditoria/compactação de prompts (ver
[Auditor e compactador de prompts (Fase 7)](#auditor-e-compactador-de-prompts-fase-7)).

### Exemplos de requisição

```bash
curl -X POST http://127.0.0.1:8000/api/v1/tokens/analisar \
  -H "Content-Type: application/json" \
  -d '{"texto": "Texto para analisar", "modelo": "gpt-4o", "incluir_token_ids": false}'
```

```bash
curl -X POST http://127.0.0.1:8000/api/v1/tokens/dividir \
  -H "Content-Type: application/json" \
  -d '{"texto": "Texto longo...", "modelo": "gpt-4o", "limite_tokens": 100, "sobreposicao_tokens": 10}'
```

```bash
curl -X POST http://127.0.0.1:8000/api/v1/tokens/comparar-modelos \
  -H "Content-Type: application/json" \
  -d '{"texto": "Texto para comparar", "modelos": ["gpt-4o", "o3", "gpt-4"]}'
```

```bash
curl -X POST http://127.0.0.1:8000/api/v1/custos/estimar \
  -H "Content-Type: application/json" \
  -d '{"modelo": "gpt-4o", "tokens_entrada": 115, "tokens_saida": 100}'
```

```bash
curl "http://127.0.0.1:8000/api/v1/historico?tipo_operacao=analise&limite=10"
```

```bash
curl "http://127.0.0.1:8000/api/v1/historico/resumo"
```

Erros de regra de negócio (texto vazio, limites inválidos, modelo de preço inexistente
etc.) retornam HTTP 422 com uma mensagem clara em português no campo `detail`, sem expor
stack trace.

## Docker Compose (Fase 5)

### Objetivo

Empacotar a API e o PostgreSQL em uma stack Docker reproduzível, totalmente
independente de qualquer container já existente na máquina. Esta stack **não** usa,
altera, para nem remove os containers externos `my-postgres` (publicado em `5433`) e
`my-pgadmin` (publicado em `15432`) — ela sobe seus próprios serviços, com nomes,
rede e volume exclusivos.

Todos os comandos abaixo assumem Git Bash.

### Pré-requisitos

- Docker Desktop instalado e em execução.
- Docker Compose v2 (`docker compose`, já incluído no Docker Desktop).

### Configuração do `.env.docker`

Copie o modelo e ajuste a senha (o arquivo `.env.docker` nunca deve ser commitado —
já está listado em `.gitignore`):

```bash
cp .env.docker.example .env.docker
```

Conteúdo do `.env.docker.example`:

```
POSTGRES_DB=token_intelligence
POSTGRES_USER=token_app
POSTGRES_PASSWORD=altere_esta_senha
POSTGRES_HOST_PORT=5434
API_HOST_PORT=8000
DATABASE_ECHO=false
SALVAR_TEXTO_COMPLETO=false
```

Edite `POSTGRES_PASSWORD` com uma senha real antes de subir a stack.

### Construção da imagem

```bash
docker compose --env-file .env.docker build
```

### Inicialização

```bash
docker compose --env-file .env.docker up --build -d
```

Isso sobe dois serviços:

| Serviço | Container | Porta host | Porta interna |
| --- | --- | --- | --- |
| `postgres` | `token-intelligence-postgres` | `5434` | `5432` |
| `api` | `token-intelligence-api` | `8000` | `8000` |

O serviço `api` só inicia depois que o `postgres` reportar saúde (`pg_isready`). Ao
iniciar, o `docker-entrypoint.sh` aguarda o banco, executa
`uv run alembic upgrade head` automaticamente e só então inicia a API — sem uso de
`Base.metadata.create_all`.

### Verificando o status

```bash
docker compose --env-file .env.docker ps
```

### Logs

```bash
docker compose --env-file .env.docker logs --no-color api
docker compose --env-file .env.docker logs --no-color postgres
docker compose --env-file .env.docker logs -f api   # acompanhar em tempo real
```

### Rebuild após alterar código ou dependências

```bash
docker compose --env-file .env.docker up --build -d
```

### Parada

```bash
docker compose --env-file .env.docker down
```

Isso **mantém** o volume `token_intelligence_postgres_data` — os dados persistem
entre reinicializações.

### Health checks

- PostgreSQL: `pg_isready -U $POSTGRES_USER -d $POSTGRES_DB` dentro do container.
- API: `GET /health`, tanto via `HEALTHCHECK` da imagem quanto no `compose.yaml`.

```bash
curl -f http://localhost:8000/health
curl -f http://localhost:8000/
```

### Migrações

As migrações do Alembic rodam automaticamente a cada `docker compose up` (dentro do
`docker-entrypoint.sh`). Para executar manualmente dentro do container já em
execução:

```bash
docker compose --env-file .env.docker exec api uv run alembic upgrade head
docker compose --env-file .env.docker exec api uv run alembic current
```

### Acesso à API

- API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Acesso ao PostgreSQL

- **Pelo Windows/host** (psql, DBeaver, pgAdmin externo etc.): `localhost:5434`,
  usando `POSTGRES_USER`/`POSTGRES_PASSWORD`/`POSTGRES_DB` definidos em
  `.env.docker`.
- **Pela API dentro do Compose**: hostname `postgres`, porta `5432` (rede interna
  `token-intelligence-network`) — nunca `localhost`, pois cada container tem sua
  própria rede de loopback.

Essas são conexões diferentes: a porta `5434` é a publicada no host para acesso
externo; a porta `5432` só existe dentro da rede Docker do projeto.

### Persistência do volume

Os dados do PostgreSQL ficam no volume nomeado `token_intelligence_postgres_data`,
declarado no `compose.yaml`. Ele sobrevive a:

```bash
docker compose --env-file .env.docker down
```

⚠️ **Aviso importante:** o comando abaixo **apaga permanentemente** todos os dados
da stack (histórico de processamentos incluído):

```bash
docker compose --env-file .env.docker down -v
```

Use `-v` apenas quando quiser descartar o banco intencionalmente.

### Backup básico

```bash
docker compose --env-file .env.docker exec -T postgres \
  pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > backup_token_intelligence.sql
```

### Restauração (executar manualmente, com cautela)

```bash
cat backup_token_intelligence.sql | \
docker compose --env-file .env.docker exec -T postgres \
  psql -U "$POSTGRES_USER" "$POSTGRES_DB"
```

### Solução de problemas

- **`docker compose` reclama de variável ausente** — confirme que `.env.docker`
  existe (`cp .env.docker.example .env.docker`) e que o comando usa
  `--env-file .env.docker`.
- **API reinicia em loop** — veja os logs (`docker compose --env-file .env.docker
  logs api`); geralmente indica que o PostgreSQL ainda não está saudável ou que a
  migração falhou.
- **`password authentication failed`** — a senha em `.env.docker` não confere com o
  volume já existente; se a senha mudou após o volume já ter sido criado, remova o
  volume (`down -v`, apagando os dados) ou recrie com a senha original.
- **Porta `5434` ou `8000` já em uso** — ajuste `POSTGRES_HOST_PORT`/`API_HOST_PORT`
  em `.env.docker` para portas livres.
- **Migrações não aplicadas** — confira os logs do serviço `api`; o
  `docker-entrypoint.sh` interrompe a inicialização com uma mensagem clara se
  `alembic upgrade head` falhar.

## Configuração do PostgreSQL (Fase 4)

### Requisitos

- PostgreSQL 14 ou superior acessível localmente (ou via Docker de terceiros, já que
  esta fase ainda não inclui `docker-compose.yml` próprio).
- Driver `psycopg` versão 3 (já incluído nas dependências do projeto via `uv sync`).

### Criação do banco

```bash
# Usando o cliente psql
psql -U postgres -h localhost -c "CREATE DATABASE token_intelligence;"
```

### Configuração do `.env`

Copie o modelo e ajuste a senha real (o arquivo `.env` nunca deve ser commitado —
já está listado em `.gitignore`):

```bash
cp .env.example .env
```

Conteúdo esperado:

```
DATABASE_URL=postgresql+psycopg://postgres:altere_a_senha@localhost:5432/token_intelligence
DATABASE_ECHO=false
SALVAR_TEXTO_COMPLETO=false
```

As configurações são carregadas por `app/config/settings.py` via `pydantic-settings`,
lendo tanto variáveis de ambiente quanto o arquivo `.env`.

### Execução das migrações

```bash
uv run alembic upgrade head
uv run alembic current
uv run alembic history
```

A migração inicial (`alembic/versions/d4f1a1c9b2e3_criar_tabela_processamentos.py`)
cria a tabela `processamentos` com todos os índices descritos abaixo. A URL de conexão
usada pelo Alembic vem sempre de `app/config/settings.py` (nunca de `alembic.ini`), para
não deixar credenciais em texto fixo no repositório.

### Estrutura da tabela `processamentos`

Guarda métricas e metadados de cada operação (`analise`, `divisao`, `comparacao`,
`estimativa_custo`), com origem (`api` ou `cli`), custos em `Numeric` de alta precisão e
um campo `metadados` em JSONB. Índices em `criado_em`, `tipo_operacao`, `origem`,
`modelo_solicitado`, `sucesso` e `texto_hash` aceleram as consultas do histórico.

### Política de privacidade do texto

Por padrão, **o texto completo processado nunca é armazenado**. A plataforma guarda
apenas:

- `texto_hash`: SHA-256 do texto normalizado (permite detectar reprocessamentos sem
  reconstruir o conteúdo original);
- `texto_preview`: os primeiros 200 caracteres do texto.

A variável `SALVAR_TEXTO_COMPLETO` permanece `false` por padrão e, nesta fase, ainda não
existe uma coluna de texto completo — ela é reservada para uma futura fase que precisará
de uma decisão explícita sobre retenção de dados. `token_ids` nunca é gravado no banco.

### Resiliência a falhas de conexão

Se o PostgreSQL estiver indisponível no momento de uma chamada à API, a operação
principal (análise, divisão, comparação ou estimativa) continua respondendo
normalmente — apenas o registro de histórico falha, é registrado em log com
`logging` (sem stack trace ao cliente e sem expor `DATABASE_URL` ou senha) e a falha
nunca é escondida silenciosamente.

### Solução de problemas de conexão

- `psycopg.OperationalError: connection failed` — confirme que o PostgreSQL está no ar
  (`pg_isready -h localhost -p 5432`) e que usuário/senha em `DATABASE_URL` estão
  corretos.
- `password authentication failed` — a senha em `DATABASE_URL` não confere com a do
  usuário no PostgreSQL; ajuste o `.env` (nunca coloque a senha real em `.env.example`
  ou no `alembic.ini`).
- `relation "processamentos" does not exist` — as migrações ainda não foram aplicadas;
  rode `uv run alembic upgrade head`.
- Testes de integração (`tests/integration/`) marcados `@pytest.mark.integration` são
  ignorados automaticamente (skip) quando `DATABASE_URL` não está acessível — isso é
  esperado em ambientes sem PostgreSQL configurado.

## Camada analítica (Fase 6)

### Objetivo e arquitetura

Modelo estrela em PostgreSQL, no schema `analytics`, derivado (nunca copiado à mão)
da tabela operacional `processamentos` — sem alterá-la. Todo o SQL vive em
`analytics/sql/01..07` (fonte única de verdade); a migração Alembic
(`alembic/versions/d93bc6ab6522_criar_camada_analytics.py`) apenas lê e executa os
arquivos `01` a `05`. Documentação completa em [`analytics/README.md`](analytics/README.md).

### Modelo estrela

```
dCalendario[data_id]   1:* fProcessamentos[data_id]
dModelo[modelo_id]     1:* fProcessamentos[modelo_id]
dOperacao[operacao_id] 1:* fProcessamentos[operacao_id]
dOrigem[origem_id]     1:* fProcessamentos[origem_id]
dStatus[status_id]     1:* fProcessamentos[status_id]
```

Direção de filtro sempre de dimensão para fato, sem relacionamento entre dimensões.
Detalhes completos (grão, chaves especiais `id = 0`, o que a fato **não** contém) em
[`analytics/docs/modelo_estrela.md`](analytics/docs/modelo_estrela.md) e
[`analytics/docs/dicionario_dados.md`](analytics/docs/dicionario_dados.md).

### Atualização da camada (refresh)

A carga é incremental e idempotente (`INSERT ... ON CONFLICT`, nunca trunca/recarrega
a fato inteira), via a função `analytics.refresh_modelo_analitico()`. Duas formas de
executá-la:

```bash
uv run python scripts/refresh_analytics.py
```

```bash
curl -X POST http://127.0.0.1:8000/api/v1/analytics/atualizar
curl http://127.0.0.1:8000/api/v1/analytics/status
```

`POST /api/v1/analytics/atualizar` é um endpoint administrativo **ainda sem
autenticação** nesta fase — deve ser protegido antes de qualquer uso em produção.
Cada execução fica registrada em `analytics.controle_carga`, consultável por
`GET /api/v1/analytics/status`.

### Conexão do Power BI

O Power BI Desktop roda fora do Docker Compose e sempre se conecta pela porta
publicada no host, nunca pelo hostname interno do Compose:

| Ambiente | Servidor para o Power BI |
| --- | --- |
| PostgreSQL local | `localhost:5433` |
| Stack Docker Compose deste projeto | `localhost:5434` |

Guia completo, com exemplos de código M usando os parâmetros `pServidor`/`pBanco`
(nunca com usuário/senha no código), em
[`analytics/docs/guia_conexao_powerbi.md`](analytics/docs/guia_conexao_powerbi.md).

### Tabelas e views

`d_calendario`, `d_modelo`, `d_operacao`, `d_origem`, `d_status`, `f_processamentos` e
`controle_carga`, além das views de consumo `analytics.vw_powerbi_processamentos`,
`vw_powerbi_resumo_diario`, `vw_powerbi_resumo_mensal` e `vw_powerbi_textos_repetidos`.
Consultas prontas para "Consulta SQL" no Power BI em
[`analytics/sql/07_powerbi_source_queries.sql`](analytics/sql/07_powerbi_source_queries.sql).

### Medidas DAX

Arquivos `.dax` em [`analytics/dax/`](analytics/dax/), agrupados por tema
(`medidas_base`, `medidas_tokens`, `medidas_custos`, `medidas_desempenho`,
`medidas_qualidade`) — total de processamentos, tokens, custos, taxa de sucesso/erro,
taxa de fallback, variação mês a mês, entre outras.

### Páginas sugeridas

Visão Executiva, Tokens e Custos, Desempenho e Qualidade, Auditoria — detalhado em
[`analytics/docs/indicadores_powerbi.md`](analytics/docs/indicadores_powerbi.md).

### Diferença entre ambiente local e Docker

Assim como o restante da plataforma, a camada analítica não precisa de configuração
própria: ela usa a mesma `DATABASE_URL` de `app/config/settings.py`/`.env` (local,
porta `5433`/`5432` conforme seu PostgreSQL) ou a injetada pelo `compose.yaml` dentro
da stack Docker (porta interna `postgres:5432`, publicada em `localhost:5434`). O
Power BI, rodando no Windows, sempre usa a porta publicada no host — nunca o hostname
interno do Compose (ver seção anterior).

### Solução de problemas

- **Tabelas do schema `analytics` não aparecem no Power BI** — rode
  `uv run alembic upgrade head`.
- **Dados desatualizados** — rode `scripts/refresh_analytics.py` (ou
  `POST /api/v1/analytics/atualizar`) antes de atualizar o relatório no Power BI.
- **Erro 500 em `/api/v1/analytics/atualizar` ou `/status`** — geralmente indica que a
  migração da camada analítica ainda não foi aplicada, ou que o PostgreSQL está
  inacessível; a resposta nunca expõe a `DATABASE_URL` nem detalhes internos.
- Mais detalhes em [`analytics/docs/guia_conexao_powerbi.md`](analytics/docs/guia_conexao_powerbi.md).

## Auditor e compactador de prompts (Fase 7)

### Objetivo e limitações

Auditar e compactar prompts **localmente, por regras de texto**, sem tradução, sem
embeddings, sem banco vetorial e **sem nenhuma chamada de IA externa** (OpenAI,
Anthropic/Claude ou qualquer outra). O compactador **não promete preservação perfeita
de significado** — o resultado é sempre apresentado como sugestão, com avisos de risco,
e a API/CLI nunca substituem o texto original automaticamente.

### Níveis de compactação

| Nível | Risco | O que faz |
| --- | --- | --- |
| `conservador` | baixo | Remove espaços duplicados, linhas vazias excessivas, pontuação repetida, palavras consecutivas duplicadas, espaços antes/depois de pontuação e parênteses, e saudações isoladas simples. |
| `moderado` | médio | Inclui o conservador + simplifica expressões redundantes configuradas (ex.: "gostaria que você pudesse" é removido). |
| `agressivo` | alto | Inclui o moderado + remoções mais amplas (introduções/conclusões redundantes). Sempre exibe aviso de risco alto. |

Cada nível inclui as regras dos níveis anteriores. Se o texto compactado não reduzir a
quantidade de tokens em relação ao original, o texto original é mantido e
`compactacao_aplicada` retorna `false` — nunca é apresentada uma "economia" falsa.

### Preservação de termos essenciais

Antes de qualquer regra ser aplicada, `app/core/protected_terms.py` protege (via
marcadores opacos, restaurados ao final): números, datas, percentuais, valores
monetários, URLs, caminhos de arquivo, `host:porta`, nomes entre aspas, blocos de
código, identificadores com underscore ou ponto, identificadores camelCase, palavras
totalmente em maiúsculas, e os termos técnicos configurados em
`app/config/protected_terms.json` (mais os informados em `termos_protegidos` na
requisição/CLI). Exemplos que nunca são alterados: `fConsumoConsolidado`,
`BITS_COUNT=32`, `Auto Date/Time`, `2026-07-19`, `R$ 1.500,00`, `localhost:5433`,
`analytics.f_processamentos`.

### Exemplo

Texto de entrada:

```
Por favor, gostaria que você pudesse realizar uma análise detalhada deste relatório
e depois de analisar me informar quais são os principais problemas encontrados.
```

Resultado (nível moderado, modelo `gpt-4o`): 27 tokens → 18 tokens (redução de
33,33%), com o trecho "gostaria que você pudesse" removido e "depois de analisar"
removido; risco médio; `compactacao_aplicada: true`.

### CLI

Opções 5 (Auditar prompt), 6 (Compactar prompt) e 7 (Comparar níveis de compactação) —
ver [Execução](#execução). A opção 6 sempre pergunta se o resultado é aprovado antes de
encerrar; nada é sobrescrito automaticamente.

### API

```bash
curl -X POST http://127.0.0.1:8000/api/v1/prompts/auditar \
  -H "Content-Type: application/json" \
  -d '{"texto": "Por favor, gostaria que você pudesse revisar isso.", "modelo": "gpt-4o"}'
```

```bash
curl -X POST http://127.0.0.1:8000/api/v1/prompts/compactar \
  -H "Content-Type: application/json" \
  -d '{"texto": "Por favor, gostaria que você pudesse revisar isso.", "modelo": "gpt-4o", "nivel": "moderado"}'
```

```bash
curl -X POST http://127.0.0.1:8000/api/v1/prompts/comparar-compactacao \
  -H "Content-Type: application/json" \
  -d '{"texto": "Por favor, gostaria que você pudesse revisar isso.", "modelo": "gpt-4o"}'
```

```bash
curl -X POST http://127.0.0.1:8000/api/v1/prompts/aprovar \
  -H "Content-Type: application/json" \
  -d '{"compactacao_id": "<id retornado por /compactar>"}'
```

### Banco de dados

Migração `alembic/versions/e7f1c9a2b4d6_criar_tabela_compactacoes_prompt.py` cria a
tabela `compactacoes_prompt`, com FK opcional para `processamentos.id`. Assim como
`processamentos`, **nunca guarda o texto completo nem `token_ids`** — apenas hash
SHA-256 e preview de 200 caracteres do texto original e do compactado. Novos tipos de
operação em `processamentos`: `auditoria_prompt`, `compactacao_prompt`,
`comparacao_compactacao`.

### Camada analytics e Power BI

Migração `alembic/versions/f3a8d2c6b1e9_criar_camada_analytics_compactacao.py` (lê
`analytics/sql/08..11`) adiciona a dimensão `analytics.d_nivel_compactacao`, a fato
`analytics.f_compactacoes_prompt`, as views `vw_powerbi_compactacoes`,
`vw_powerbi_resumo_compactacao_diario` e `vw_powerbi_resumo_compactacao_mensal`, e a
função `analytics.refresh_compactacoes_prompt()` — **separada** de
`refresh_modelo_analitico()`, para não alterar sua assinatura nem seu comportamento.
Executável junto com o refresh existente:

```bash
uv run python scripts/refresh_analytics.py
```

```bash
curl -X POST http://127.0.0.1:8000/api/v1/analytics/atualizar-compactacoes
curl http://127.0.0.1:8000/api/v1/analytics/status-compactacoes
```

Medidas DAX em [`analytics/dax/medidas_compactacao.dax`](analytics/dax/medidas_compactacao.dax)
(Total Compactações, Tokens Economizados, Taxa de Aprovação %, Compactações sem
Benefício, entre outras).

### Como adicionar novas regras de compactação

Edite `app/config/compression_rules.json` — cada nível (`conservador`, `moderado`,
`agressivo`) aceita `substituicoes` (lista de `{"de": "...", "para": "..."}`) e
`remocoes` (lista de frases a remover). Não é necessário alterar código Python.

### Como adicionar termos protegidos

Edite `app/config/protected_terms.json` (lista `termos`), ou informe termos adicionais
pontualmente via o campo `termos_protegidos` na requisição da API/CLI — em ambos os
casos, sem alterar código.

### Riscos e aprovação humana

- O nível agressivo **nunca** é aplicado automaticamente e sempre exibe aviso de risco
  alto.
- `POST /api/v1/prompts/comparar-compactacao` nunca escolhe o agressivo como
  "recomendado" apenas por ele reduzir mais tokens — isso fica explícito em
  `melhor_reducao` (que pode ser o agressivo) versus `recomendado` (que pondera risco).
- A aprovação (`POST /api/v1/prompts/aprovar`) é sempre um passo humano separado e
  explícito; não há nenhum mecanismo de substituição automática do texto original.

## Testes

```bash
uv run pytest -v
```

Os testes unitários (incluindo os da API) usam SQLite em memória, isolado por teste, e
nunca dependem de um PostgreSQL real — a sessão de banco é sobrescrita via
`app.dependency_overrides` (ver `tests/conftest.py`). A coluna `metadados` usa um tipo
JSON genérico que vira JSONB apenas no PostgreSQL, sem esconder essa diferença de
dialeto.

Os testes de integração com PostgreSQL real ficam em `tests/integration/` e são
ignorados (skip) automaticamente quando `DATABASE_URL` não está acessível. Para
executá-los explicitamente após configurar o `.env` e aplicar as migrações:

```bash
uv run pytest -m integration -v
```

Nenhum teste faz chamada de rede externa além da conexão opcional com o PostgreSQL
local.

## Exemplos

### Estimador de custos

```python
from decimal import Decimal
from app.services.cost_estimator import estimar_custo_por_modelo

resultado = estimar_custo_por_modelo(
    tokens_entrada=1_000_000,
    tokens_saida=250_000,
    modelo="gpt-4o",
)
print(resultado.custo_total)  # Decimal calculado a partir do JSON de preços
```

### Divisor de textos por tokens

```python
from app.core.splitter import dividir_texto_por_tokens

blocos = dividir_texto_por_tokens(
    texto="texto muito longo...",
    modelo="gpt-4o",
    limite_tokens=500,
    sobreposicao=50,
)
```

### Comparador de modelos

```python
from app.services.model_comparator import comparar_modelos

resultados = comparar_modelos(
    texto="Ola mundo",
    modelos=["gpt-4o", "gpt-3.5-turbo", "modelo-inexistente"],
)
```

## Aviso sobre preços

Os valores em `app/config/model_prices.json` são **demonstrativos** e servem apenas para exemplificar o
funcionamento do estimador de custos. Eles **não refletem preços comerciais reais** e podem estar
desatualizados. Atualize o arquivo com os preços vigentes antes de qualquer uso além de testes.

## Roadmap

- Próximas fases (ainda pendentes): tradução automática, compressão semântica e
  chamadas externas de IA (OpenAI/Anthropic) — fora de escopo até que haja uma decisão
  explícita sobre uso de serviços externos.

## Limitações atuais

- O auditor e o compactador de prompts (Fase 7) usam **apenas regras locais de texto**;
  não há tradução, compressão semântica, embeddings, banco vetorial ou qualquer chamada
  de IA externa. O compactador não garante preservação perfeita de significado — todo
  resultado é uma sugestão sujeita a aprovação humana.
- O histórico e a camada analítica dependem de um PostgreSQL configurado via `.env`;
  sem ele, as operações da API continuam funcionando normalmente, mas nada é
  persistido (ver [Resiliência a falhas de conexão](#resiliência-a-falhas-de-conexão)).
- O menu CLI ainda não registra suas operações no histórico nem na camada analítica
  (apenas as chamadas via API o fazem nesta fase).
- Os preços de modelos são apenas exemplos e precisam ser mantidos manualmente.
- `POST /api/v1/analytics/atualizar` e `POST /api/v1/analytics/atualizar-compactacoes`
  são endpoints administrativos ainda sem autenticação — devem ser protegidos antes de
  qualquer uso em produção.
- A camada analítica é preenchida sob demanda (`scripts/refresh_analytics.py` ou os
  endpoints `/atualizar*`), não automaticamente a cada processamento; não há agendador
  embutido nesta fase.
- Se a persistência de uma compactação falhar (ex.: PostgreSQL indisponível), a API
  ainda responde normalmente, mas o `compactacao_id` retornado não existirá no banco —
  uma aprovação posterior para esse ID retornará 404.

## Aviso sobre preços (API)

Assim como no menu CLI, os valores retornados por `POST /api/v1/custos/estimar` são
**demonstrativos** (ver `app/config/model_prices.json`) e vêm acompanhados do campo
`aviso` na resposta, alertando que não refletem preços comerciais reais.
# token-intelligence-platform
