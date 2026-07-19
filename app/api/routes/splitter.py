"""Rota de divisão de texto em blocos por quantidade de tokens."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import obter_sessao_bd
from app.core.splitter import dividir_texto_por_tokens
from app.schemas.splitter_schemas import (
    BlocoTextoResponse,
    DividirTextoRequest,
    DividirTextoResponse,
)
from app.services.processing_history import registrar_divisao

router = APIRouter(prefix="/api/v1/tokens", tags=["Tokens"])


@router.post(
    "/dividir",
    response_model=DividirTextoResponse,
    summary="Divide um texto em blocos respeitando um limite de tokens",
)
def dividir(
    requisicao: DividirTextoRequest,
    sessao: Session = Depends(obter_sessao_bd),
) -> DividirTextoResponse:
    """Executa a divisão de texto reutilizando app/core/splitter.py."""
    blocos = dividir_texto_por_tokens(
        texto=requisicao.texto,
        modelo=requisicao.modelo,
        limite_tokens=requisicao.limite_tokens,
        sobreposicao=requisicao.sobreposicao_tokens,
    )

    total_tokens_original = blocos[-1].token_final + 1

    registrar_divisao(
        sessao=sessao,
        texto=requisicao.texto,
        modelo=requisicao.modelo,
        limite_tokens=requisicao.limite_tokens,
        sobreposicao_tokens=requisicao.sobreposicao_tokens,
        total_blocos=len(blocos),
        total_tokens_original=total_tokens_original,
    )

    return DividirTextoResponse(
        modelo=requisicao.modelo,
        total_blocos=len(blocos),
        total_tokens_original=total_tokens_original,
        blocos=[BlocoTextoResponse(**bloco.__dict__) for bloco in blocos],
    )
