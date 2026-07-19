# Guia de conexão do Power BI ao PostgreSQL

## Portas: local vs. Docker

O Power BI Desktop roda no Windows, fora do Docker Compose, então ele **sempre**
se conecta pela porta publicada no host — nunca pelo hostname interno do Compose
(`postgres`), que só existe dentro da rede `token-intelligence-network`.

| Ambiente                              | Servidor para o Power BI  |
|----------------------------------------|-----------------------------|
| PostgreSQL local (fora do Docker)       | `localhost:5433` (padrão de `app/config/settings.py`) |
| Stack Docker Compose deste projeto     | `localhost:5434` (porta publicada no `compose.yaml`)   |

Banco: `token_intelligence` (ajuste conforme seu `.env`/`.env.docker`).

Nunca use `postgres:5432` no Power BI — esse endereço só é resolvido de dentro
dos containers da stack.

## Passo a passo — Obter Dados

1. Power BI Desktop → **Obter Dados** → **Banco de Dados PostgreSQL**.
2. Servidor: `localhost:5434` (Docker) ou `localhost:5433` (local), conforme a tabela acima.
3. Banco de dados: `token_intelligence`.
4. Modo de conectividade: **Import** (recomendado para o volume desta fase) ou
   **DirectQuery**, se preferir dados sempre atualizados sem precisar dar refresh.
5. No navegador, selecione o schema `analytics` e marque as tabelas/views:
   `d_calendario`, `d_modelo`, `d_operacao`, `d_origem`, `d_status`,
   `f_processamentos` (ou as views `vw_powerbi_*`, conforme a necessidade do relatório).
6. Informe usuário e senha do PostgreSQL quando solicitado pelo Power BI — **nunca
   digite a senha dentro do código M** (ver seção seguinte).

## Parâmetros do Power Query (M) — sem credenciais

Crie dois parâmetros no Power Query: `pServidor` e `pBanco`. A senha nunca entra
no código M; o Power BI a gerencia separadamente através das credenciais salvas
da fonte de dados.

```m
// Parâmetro: pServidor (Texto)
// Valor de exemplo local:   "localhost:5433"
// Valor de exemplo Docker:  "localhost:5434"

// Parâmetro: pBanco (Texto)
// Valor de exemplo: "token_intelligence"
```

Consulta usando os parâmetros (substitui a tabela/view conforme a necessidade):

```m
let
    Origem = PostgreSQL.Database(pServidor, pBanco),
    schemaAnalytics = Origem{[Schema = "analytics", Item = "f_processamentos"]}[Data]
in
    schemaAnalytics
```

Exemplo lendo diretamente uma view de resumo:

```m
let
    Origem = PostgreSQL.Database(pServidor, pBanco),
    resumoDiario = Origem{[Schema = "analytics", Item = "vw_powerbi_resumo_diario"]}[Data]
in
    resumoDiario
```

## Relacionamentos no modelo

Depois de importar as tabelas, configure no Power BI (view Modelo):

```
dCalendario[data_id]   1:* fProcessamentos[data_id]
dModelo[modelo_id]     1:* fProcessamentos[modelo_id]
dOperacao[operacao_id] 1:* fProcessamentos[operacao_id]
dOrigem[origem_id]     1:* fProcessamentos[origem_id]
dStatus[status_id]     1:* fProcessamentos[status_id]
```

- Direção de filtro única: da dimensão para a fato.
- Marque `dCalendario` como tabela de datas (clique direito → "Marcar como
  tabela de datas" → coluna `data`).
- Oculte as colunas `*_id` na visão de relatório (mantendo-as no modelo, para
  os relacionamentos continuarem funcionando).
- Renomeie as tabelas no modelo para `dCalendario`, `dModelo`, `dOperacao`,
  `dOrigem`, `dStatus` e `fProcessamentos`, para que as medidas DAX em
  `analytics/dax/*.dax` funcionem sem alteração.

## Atualizando os dados

Antes de dar refresh no Power BI, atualize a camada analítica no PostgreSQL:

```bash
uv run python scripts/refresh_analytics.py
```

ou via API (ver `analytics/README.md`):

```
POST /api/v1/analytics/atualizar
```

## Solução de problemas

- **Erro de conexão recusada**: confira se o PostgreSQL está no ar
  (`docker compose --env-file .env.docker ps` ou o serviço local) e se a porta
  usada é a publicada no host (5433 local / 5434 Docker), não `postgres:5432`.
- **Tabelas do schema `analytics` não aparecem no navegador**: rode
  `uv run alembic upgrade head` para criar o schema antes de conectar.
- **Dados desatualizados no relatório**: rode `scripts/refresh_analytics.py`
  (ou `POST /api/v1/analytics/atualizar`) e depois "Atualizar" no Power BI.
- **Relacionamentos não funcionam / totais errados**: confirme que as colunas
  `*_id` não foram removidas do modelo (apenas ocultadas) e que a direção de
  filtro está configurada como única (dimensão → fato).
