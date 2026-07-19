# Imagem da API da Token Intelligence Platform.
# Usa uv para instalar dependências e executar a aplicação (nunca pip diretamente).

FROM python:3.13-slim

# Instala o uv copiando o binário oficial (sem exigir curl/pip na imagem final).
COPY --from=ghcr.io/astral-sh/uv:0.11.29 /uv /uvx /usr/local/bin/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Dependências do sistema: curl para o healthcheck, postgresql-client para o
# docker-entrypoint.sh aguardar o PostgreSQL (pg_isready) antes de migrar.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Instala as dependências primeiro, aproveitando o cache do Docker: esta
# camada só é reconstruída quando pyproject.toml ou uv.lock mudam.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# Copia o restante do código somente depois das dependências instaladas.
COPY . .

RUN uv sync --frozen --no-dev

# Usuário não root para execução da API.
RUN groupadd --system app && useradd --system --gid app --home-dir /app app \
    && chown -R app:app /app
USER app

COPY --chmod=755 docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["docker-entrypoint.sh"]
