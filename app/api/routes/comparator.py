"""Rota de comparação de tokenização entre modelos."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import obter_sessao_bd
from app.schemas.comparator_schemas import (
    CompararModelosRequest,
    CompararModelosResponse,
    ResultadoComparacaoResponse,
)
from app.services.model_comparator import comparar_modelos
from app.services.processing_history import registrar_comparacao

router = APIRouter(prefix="/api/v1/tokens", tags=["Tokens"])

AVISO_FALLBACK = (
    "Modelo não reconhecido pelo tiktoken; foi utilizado fallback para o200k_base."
)


@router.post(
    "/comparar-modelos",
    response_model=CompararModelosResponse,
    summary="Compara a tokenização de um texto entre diferentes modelos",
)
def comparar(
    requisicao: CompararModelosRequest,
    sessao: Session = Depends(obter_sessao_bd),
) -> CompararModelosResponse:
    """Executa a comparação reutilizando app/services/model_comparator.py."""
    resultados = comparar_modelos(texto=requisicao.texto, modelos=requisicao.modelos)

    registrar_comparacao(sessao=sessao, texto=requisicao.texto, resultados=resultados)

    return CompararModelosResponse(
        resultados=[
            ResultadoComparacaoResponse(
                **resultado.__dict__,
                aviso=AVISO_FALLBACK if resultado.fallback_utilizado else None,
            )
            for resultado in resultados
        ]
    )
