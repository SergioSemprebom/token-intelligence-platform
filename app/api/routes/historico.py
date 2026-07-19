"""Rotas de consulta ao histórico de processamentos."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import obter_sessao_bd
from app.database.models.processamento import TIPOS_OPERACAO_VALIDOS
from app.repositories.processamento_repository import ProcessamentoRepository
from app.schemas.historico_schemas import (
    HistoricoPaginadoResponse,
    HistoricoResumoResponse,
    ProcessamentoResponse,
)

router = APIRouter(prefix="/api/v1/historico", tags=["Histórico"])


@router.get(
    "",
    response_model=HistoricoPaginadoResponse,
    summary="Lista o histórico de processamentos de forma paginada",
)
def listar_historico(
    limite: int = Query(default=20, gt=0, le=200),
    offset: int = Query(default=0, ge=0),
    tipo_operacao: str | None = Query(default=None),
    modelo: str | None = Query(default=None),
    sucesso: bool | None = Query(default=None),
    data_inicio: datetime | None = Query(default=None),
    data_fim: datetime | None = Query(default=None),
    sessao: Session = Depends(obter_sessao_bd),
) -> HistoricoPaginadoResponse:
    """Lista processamentos com filtros e paginação opcionais."""
    if tipo_operacao is not None and tipo_operacao not in TIPOS_OPERACAO_VALIDOS:
        raise ValueError(
            f"tipo_operacao inválido: '{tipo_operacao}'. "
            f"Valores aceitos: {sorted(TIPOS_OPERACAO_VALIDOS)}."
        )

    if data_inicio is not None and data_fim is not None and data_inicio > data_fim:
        raise ValueError("data_inicio não pode ser posterior a data_fim.")

    repositorio = ProcessamentoRepository(sessao)
    filtros = {
        "tipo_operacao": tipo_operacao,
        "modelo_solicitado": modelo,
        "sucesso": sucesso,
        "data_inicio": data_inicio,
        "data_fim": data_fim,
    }

    resultados = repositorio.listar(limite=limite, offset=offset, **filtros)
    total = repositorio.contar(**filtros)

    return HistoricoPaginadoResponse(
        total=total,
        limite=limite,
        offset=offset,
        resultados=[ProcessamentoResponse.model_validate(item) for item in resultados],
    )


@router.get(
    "/resumo",
    response_model=HistoricoResumoResponse,
    summary="Retorna métricas agregadas do histórico de processamentos",
)
def obter_resumo_historico(
    sessao: Session = Depends(obter_sessao_bd),
) -> HistoricoResumoResponse:
    """Calcula métricas agregadas de todo o histórico de processamentos."""
    resumo = ProcessamentoRepository(sessao).obter_resumo()

    return HistoricoResumoResponse(
        total_processamentos=resumo.total_processamentos,
        total_tokens_entrada=resumo.total_tokens_entrada,
        total_tokens_saida=resumo.total_tokens_saida,
        total_tokens=resumo.total_tokens,
        custo_total=resumo.custo_total,
        quantidade_sucessos=resumo.quantidade_sucessos,
        quantidade_erros=resumo.quantidade_erros,
        processamentos_por_tipo=resumo.processamentos_por_tipo,
        processamentos_por_modelo=resumo.processamentos_por_modelo,
    )


@router.get(
    "/{processamento_id}",
    response_model=ProcessamentoResponse,
    summary="Busca um processamento específico pelo identificador",
)
def buscar_processamento(
    processamento_id: uuid.UUID,
    sessao: Session = Depends(obter_sessao_bd),
) -> ProcessamentoResponse:
    """Busca um processamento pelo ID. Retorna HTTP 404 se não existir."""
    processamento = ProcessamentoRepository(sessao).buscar_por_id(processamento_id)

    if processamento is None:
        raise HTTPException(status_code=404, detail="Processamento não encontrado.")

    return ProcessamentoResponse.model_validate(processamento)
