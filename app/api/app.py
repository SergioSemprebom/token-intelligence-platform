"""Aplicação FastAPI da Token Intelligence Platform.

Expõe via HTTP as regras de negócio já existentes em app/core e
app/services, sem duplicar lógica. Para executar:

    uv run uvicorn app.api.app:app --reload
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import (
    analytics,
    comparator,
    compression,
    costs,
    dashboard,
    health,
    historico,
    splitter,
    tokens,
)

app = FastAPI(
    title="Token Intelligence Platform API",
    description=(
        "API local para análise e governança de tokens de aplicações com modelos de "
        "linguagem. Reúne contagem de tokens, divisão de textos, comparação de "
        "tokenização entre modelos, estimativa de custos, auditoria e compactação "
        "local de prompts, camada analítica para Power BI e o dashboard web "
        "multiprovedor da Fase 8."
    ),
    version="0.8.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(tokens.router)
app.include_router(splitter.router)
app.include_router(comparator.router)
app.include_router(costs.router)
app.include_router(historico.router)
app.include_router(analytics.router)
app.include_router(compression.router)
app.include_router(dashboard.router)


@app.get("/", tags=["Raiz"], summary="Informações gerais da API")
def raiz() -> dict[str, str]:
    """Retorna informações básicas sobre a API e o link para a documentação."""
    return {
        "aplicacao": "Token Intelligence Platform API",
        "versao": "0.8.0",
        "documentacao": "/docs",
        "dashboard": "/api/v1/dashboard/resumo",
    }


@app.exception_handler(ValueError)
async def tratar_value_error(request: Request, exc: ValueError) -> JSONResponse:
    """Converte violações de regras de negócio (ValueError) em resposta HTTP 422."""
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def tratar_erro_inesperado(request: Request, exc: Exception) -> JSONResponse:
    """Trata qualquer erro não previsto sem expor detalhes internos ao cliente."""
    return JSONResponse(
        status_code=500,
        content={"detail": "Erro interno inesperado. Tente novamente mais tarde."},
    )
