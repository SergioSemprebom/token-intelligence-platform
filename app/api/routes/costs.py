"""Rota de estimativa de custo de uso de tokens."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import obter_caminho_precos, obter_sessao_bd
from app.schemas.cost_schemas import EstimarCustoRequest, EstimarCustoResponse
from app.services.cost_estimator import estimar_custo_por_modelo, obter_aviso_precos
from app.services.processing_history import registrar_estimativa_custo

router = APIRouter(prefix="/api/v1/custos", tags=["Custos"])

MOEDA_PADRAO = "USD"


@router.post(
    "/estimar",
    response_model=EstimarCustoResponse,
    summary="Estima o custo de uso de tokens para um modelo",
)
def estimar(
    requisicao: EstimarCustoRequest,
    caminho_precos: Path = Depends(obter_caminho_precos),
    sessao: Session = Depends(obter_sessao_bd),
) -> EstimarCustoResponse:
    """Executa a estimativa de custo reutilizando app/services/cost_estimator.py."""
    resultado = estimar_custo_por_modelo(
        tokens_entrada=requisicao.tokens_entrada,
        tokens_saida=requisicao.tokens_saida,
        modelo=requisicao.modelo,
        caminho=caminho_precos,
    )

    registrar_estimativa_custo(
        sessao=sessao,
        modelo=resultado.modelo,
        tokens_entrada=resultado.tokens_entrada,
        tokens_saida=resultado.tokens_saida,
        custo_entrada=resultado.custo_entrada,
        custo_saida=resultado.custo_saida,
        custo_total=resultado.custo_total,
        moeda=MOEDA_PADRAO,
    )

    return EstimarCustoResponse(
        modelo=resultado.modelo,
        tokens_entrada=resultado.tokens_entrada,
        tokens_saida=resultado.tokens_saida,
        total_tokens=resultado.tokens_total,
        custo_entrada=str(resultado.custo_entrada),
        custo_saida=str(resultado.custo_saida),
        custo_total=str(resultado.custo_total),
        moeda="USD",
        aviso=obter_aviso_precos(caminho_precos),
    )
