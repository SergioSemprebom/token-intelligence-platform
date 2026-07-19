"""Rota de análise de texto por quantidade de tokens."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import obter_sessao_bd
from app.core.tokenizer import analisar_texto, obter_encoding_info
from app.schemas.token_schemas import AnalisarTextoRequest, AnalisarTextoResponse
from app.services.processing_history import registrar_analise

router = APIRouter(prefix="/api/v1/tokens", tags=["Tokens"])


@router.post(
    "/analisar",
    response_model=AnalisarTextoResponse,
    summary="Analisa um texto e retorna métricas de tokenização",
)
def analisar(
    requisicao: AnalisarTextoRequest,
    sessao: Session = Depends(obter_sessao_bd),
) -> AnalisarTextoResponse:
    """Executa a análise de tokenização reutilizando app/core/tokenizer.py."""
    resultado = analisar_texto(
        texto=requisicao.texto,
        modelo=requisicao.modelo,
        incluir_token_ids=requisicao.incluir_token_ids,
    )
    _, fallback_utilizado = obter_encoding_info(requisicao.modelo)

    registrar_analise(
        sessao=sessao,
        texto=requisicao.texto,
        resultado=resultado,
        fallback_utilizado=fallback_utilizado,
    )

    return AnalisarTextoResponse(**resultado, fallback_utilizado=fallback_utilizado)
