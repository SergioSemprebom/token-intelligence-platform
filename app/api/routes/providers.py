"""Gerenciamento seguro de provedores da Fase 8.1.

A chave administrativa nunca é persistida, registrada em log ou devolvida ao
cliente. O modo real valida a credencial diretamente na API administrativa da
OpenAI; o modo simulado permite testar a interface sem chamada externa.
"""

from __future__ import annotations

import os
from typing import Literal

import httpx
from fastapi import APIRouter
from pydantic import BaseModel, Field, SecretStr

router = APIRouter(prefix="/api/v1/providers", tags=["Provedores"])
OPENAI_USERS_URL = "https://api.openai.com/v1/organization/users"


class OpenAIConnectionRequest(BaseModel):
    nome: str = Field(min_length=3, max_length=80)
    api_key: SecretStr | None = None
    orcamento_mensal: float = Field(default=100.0, gt=0)
    moeda: Literal["USD", "BRL"] = "USD"
    modo_simulacao: bool = True


class ProviderConnectionResponse(BaseModel):
    provedor: str
    nome: str
    status: str
    credencial_mascarada: str
    orcamento_mensal: float
    moeda: str
    mensagem: str


def _mask_secret(value: str | None) -> str:
    if not value:
        return "não informada"
    if len(value) <= 8:
        return "••••••••"
    return f"{value[:5]}••••••••{value[-4:]}"


@router.get("", summary="Lista provedores e disponibilidade")
def listar_provedores() -> list[dict[str, str]]:
    return [
        {
            "nome": "OpenAI",
            "slug": "openai",
            "status": "teste_real_disponivel",
            "tipo_credencial": "Admin API Key",
        },
        {"nome": "Gemini", "slug": "gemini", "status": "planejado", "tipo_credencial": "Google Cloud"},
        {"nome": "Claude", "slug": "anthropic", "status": "planejado", "tipo_credencial": "Admin API Key"},
        {"nome": "OpenRouter", "slug": "openrouter", "status": "planejado", "tipo_credencial": "Management Key"},
    ]


@router.post(
    "/openai/testar",
    response_model=ProviderConnectionResponse,
    summary="Testa uma conexão simulada ou real com OpenAI",
)
async def testar_openai(payload: OpenAIConnectionRequest) -> ProviderConnectionResponse:
    supplied = payload.api_key.get_secret_value() if payload.api_key else None
    secret = supplied or os.getenv("OPENAI_ADMIN_API_KEY")

    if payload.modo_simulacao:
        return ProviderConnectionResponse(
            provedor="openai",
            nome=payload.nome,
            status="simulado",
            credencial_mascarada=_mask_secret(secret),
            orcamento_mensal=payload.orcamento_mensal,
            moeda=payload.moeda,
            mensagem="Conexão simulada validada. Nenhuma chamada externa foi realizada.",
        )

    if not secret:
        raise ValueError(
            "Informe uma Admin API Key da OpenAI ou configure OPENAI_ADMIN_API_KEY no arquivo .env."
        )

    headers = {"Authorization": f"Bearer {secret}", "Content-Type": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            response = await client.get(OPENAI_USERS_URL, headers=headers, params={"limit": 1})
    except httpx.TimeoutException as exc:
        raise ValueError("A OpenAI não respondeu dentro do tempo esperado.") from exc
    except httpx.HTTPError as exc:
        raise ValueError("Não foi possível estabelecer comunicação segura com a OpenAI.") from exc

    if response.status_code in {401, 403}:
        raise ValueError("Chave administrativa inválida ou sem permissão de proprietário da organização.")
    if response.status_code >= 400:
        raise ValueError(f"A OpenAI recusou o teste de conexão (HTTP {response.status_code}).")

    return ProviderConnectionResponse(
        provedor="openai",
        nome=payload.nome,
        status="conectado",
        credencial_mascarada=_mask_secret(secret),
        orcamento_mensal=payload.orcamento_mensal,
        moeda=payload.moeda,
        mensagem="Credencial administrativa validada com sucesso na OpenAI.",
    )
