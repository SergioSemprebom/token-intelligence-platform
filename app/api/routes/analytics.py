"""Rotas administrativas da camada analítica (schema `analytics`, Power BI)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.dependencies import obter_sessao_bd
from app.repositories.analytics_repository import AnalyticsRepository
from app.schemas.analytics_schemas import AnalyticsRefreshResponse, AnalyticsStatusResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])

_MENSAGEM_ERRO_BANCO = (
    "Não foi possível acessar a camada analítica. Verifique se a migração "
    "'uv run alembic upgrade head' já foi executada e se o PostgreSQL está acessível."
)


@router.post(
    "/atualizar",
    response_model=AnalyticsRefreshResponse,
    summary="Executa a carga incremental da camada analítica (Power BI)",
)
def atualizar_analytics(
    sessao: Session = Depends(obter_sessao_bd),
) -> AnalyticsRefreshResponse:
    """Executa `analytics.refresh_modelo_analitico()`.

    Endpoint administrativo ainda sem autenticação nesta fase — antes de uso
    em produção deve ser protegido (ex.: exigir usuário administrador), pois
    dispara uma carga incremental sobre todo o histórico de processamentos.
    """
    try:
        resultado = AnalyticsRepository(sessao).executar_refresh()
    except SQLAlchemyError:
        logger.error("Falha ao executar refresh da camada analítica.", exc_info=True)
        raise HTTPException(status_code=500, detail=_MENSAGEM_ERRO_BANCO) from None

    return AnalyticsRefreshResponse(
        dimensoes_modelo_inseridas=resultado.dimensoes_modelo_inseridas,
        fatos_inseridos=resultado.fatos_inseridos,
        fatos_atualizados=resultado.fatos_atualizados,
        executado_em=resultado.executado_em,
    )


@router.get(
    "/status",
    response_model=AnalyticsStatusResponse,
    summary="Consulta a última execução da carga da camada analítica",
)
def status_analytics(
    sessao: Session = Depends(obter_sessao_bd),
) -> AnalyticsStatusResponse:
    """Retorna a execução mais recente registrada em `analytics.controle_carga`."""
    try:
        ultima_carga = AnalyticsRepository(sessao).obter_ultima_carga()
    except SQLAlchemyError:
        logger.error("Falha ao consultar o status da camada analítica.", exc_info=True)
        raise HTTPException(status_code=500, detail=_MENSAGEM_ERRO_BANCO) from None

    if ultima_carga is None:
        return AnalyticsStatusResponse(
            mensagem="Nenhuma atualização da camada analítica foi executada ainda."
        )

    return AnalyticsStatusResponse(
        ultima_carga_em=ultima_carga.iniciado_em,
        status=ultima_carga.status,
        registros_inseridos=ultima_carga.registros_inseridos,
        registros_atualizados=ultima_carga.registros_atualizados,
        mensagem=ultima_carga.mensagem,
    )


@router.post(
    "/atualizar-compactacoes",
    response_model=AnalyticsRefreshResponse,
    summary="Executa a carga incremental da fato de compactações de prompt (Power BI)",
)
def atualizar_analytics_compactacoes(
    sessao: Session = Depends(obter_sessao_bd),
) -> AnalyticsRefreshResponse:
    """Executa `analytics.refresh_compactacoes_prompt()`.

    Função separada de `POST /atualizar` (que roda
    `refresh_modelo_analitico()`), para não alterar seu comportamento.
    Endpoint administrativo ainda sem autenticação nesta fase.
    """
    try:
        resultado = AnalyticsRepository(sessao).executar_refresh_compactacoes()
    except SQLAlchemyError:
        logger.error("Falha ao executar refresh da fato de compactações.", exc_info=True)
        raise HTTPException(status_code=500, detail=_MENSAGEM_ERRO_BANCO) from None

    return AnalyticsRefreshResponse(
        dimensoes_modelo_inseridas=resultado.dimensoes_modelo_inseridas,
        fatos_inseridos=resultado.fatos_inseridos,
        fatos_atualizados=resultado.fatos_atualizados,
        executado_em=resultado.executado_em,
    )


@router.get(
    "/status-compactacoes",
    response_model=AnalyticsStatusResponse,
    summary="Consulta a última execução da carga da fato de compactações de prompt",
)
def status_analytics_compactacoes(
    sessao: Session = Depends(obter_sessao_bd),
) -> AnalyticsStatusResponse:
    """Retorna a execução mais recente de `refresh_compactacoes_prompt`."""
    try:
        ultima_carga = AnalyticsRepository(sessao).obter_ultima_carga(
            processo="refresh_compactacoes_prompt"
        )
    except SQLAlchemyError:
        logger.error("Falha ao consultar o status da fato de compactações.", exc_info=True)
        raise HTTPException(status_code=500, detail=_MENSAGEM_ERRO_BANCO) from None

    if ultima_carga is None:
        return AnalyticsStatusResponse(
            mensagem="Nenhuma atualização da fato de compactações foi executada ainda."
        )

    return AnalyticsStatusResponse(
        ultima_carga_em=ultima_carga.iniciado_em,
        status=ultima_carga.status,
        registros_inseridos=ultima_carga.registros_inseridos,
        registros_atualizados=ultima_carga.registros_atualizados,
        mensagem=ultima_carga.mensagem,
    )
