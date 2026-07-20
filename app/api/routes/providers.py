"""Gerenciamento seguro de provedores da Fase 8.1.

A conexão inicial com OpenAI é simulada e usa somente uma chave fornecida na
requisição ou a variável de ambiente OPENAI_ADMIN_API_KEY. A chave nunca é
persistida, registrada em log ou devolvida ao cliente.
"""

from __future__ import annotations

import os
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field, SecretStr

router = APIRouter(prefix="/api/v1/providers", tags=["Provedores"])


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
    return f"{value[:4]}••••••••{value[-4:]}"


@router.get("", summary="Lista provedores e disponibilidade")
def listar_provedores() -> list[dict[str, str]]:
    return [
        {"nome": "OpenAI", "slug": "openai", "status": "simulacao_disponivel"},
        {"nome": "Gemini", "slug": "gemini", "status": "planejado"},
        {"nome": "Claude", "slug": "anthropic", "status": "planejado"},
        {"nome": "OpenRouter", "slug": "openrouter", "status": "planejado"},
    ]


@router.post(
    "/openai/testar",
    response_model=ProviderConnectionResponse,
    summary="Testa uma conexão simulada com OpenAI",
)
def testar_openai(payload: OpenAIConnectionRequest) -> ProviderConnectionResponse:
    supplied = payload.api_key.get_secret_value() if payload.api_key else None
    secret = supplied or os.getenv("OPENAI_ADMIN_API_KEY")

    if not payload.modo_simulacao and not secret:
        raise ValueError(
            "Informe uma chave administrativa da OpenAI ou configure OPENAI_ADMIN_API_KEY no arquivo .env."
        )

    if payload.modo_simulacao:
        status = "simulado"
        mensagem = "Conexão simulada validada. Nenhuma chamada externa foi realizada."
    else:
        status = "configurado_para_teste_real"
        mensagem = (
            "Credencial recebida com segurança. O teste real será habilitado na Fase 8.2."
        )

    return ProviderConnectionResponse(
        provedor="openai",
        nome=payload.nome,
        status=status,
        credencial_mascarada=_mask_secret(secret),
        orcamento_mensal=payload.orcamento_mensal,
        moeda=payload.moeda,
        mensagem=mensagem,
    )
