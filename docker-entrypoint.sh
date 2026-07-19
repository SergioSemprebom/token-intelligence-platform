#!/bin/sh
# Entrypoint da API da Token Intelligence Platform.
#
# 1. Aguarda o PostgreSQL ficar disponível (pg_isready).
# 2. Executa as migrações do Alembic (uv run alembic upgrade head).
# 3. Inicia a API com exec (para receber sinais corretamente).
#
# Nunca imprime senha nem a DATABASE_URL completa nos logs.

set -eu

POSTGRES_HOST="${POSTGRES_HOST:-postgres}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_DB="${POSTGRES_DB:-token_intelligence}"

TENTATIVAS_MAXIMAS=30
TENTATIVA=1

echo "Aguardando PostgreSQL em ${POSTGRES_HOST}:${POSTGRES_PORT}..."

until pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null 2>&1; do
    if [ "$TENTATIVA" -ge "$TENTATIVAS_MAXIMAS" ]; then
        echo "Erro: PostgreSQL não ficou disponível em ${POSTGRES_HOST}:${POSTGRES_PORT} após ${TENTATIVAS_MAXIMAS} tentativas." >&2
        exit 1
    fi
    TENTATIVA=$((TENTATIVA + 1))
    sleep 2
done

echo "PostgreSQL disponível. Executando migrações do Alembic..."

if ! uv run alembic upgrade head; then
    echo "Erro: falha ao executar as migrações do Alembic. Encerrando." >&2
    exit 1
fi

echo "Migrações aplicadas com sucesso. Iniciando a API..."

exec uv run uvicorn app.api.app:app --host 0.0.0.0 --port 8000
