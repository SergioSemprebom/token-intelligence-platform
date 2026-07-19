"""Schemas Pydantic dos endpoints administrativos da camada analítica."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AnalyticsRefreshResponse(BaseModel):
    """Resposta da execução da carga incremental da camada analítica."""

    dimensoes_modelo_inseridas: int = Field(
        ..., description="Modelos novos inseridos em analytics.d_modelo"
    )
    fatos_inseridos: int = Field(
        ..., description="Processamentos novos inseridos em analytics.f_processamentos"
    )
    fatos_atualizados: int = Field(
        ...,
        description="Processamentos existentes atualizados em analytics.f_processamentos",
    )
    executado_em: datetime = Field(..., description="Momento em que o refresh foi concluído")


class AnalyticsStatusResponse(BaseModel):
    """Resposta com a última execução registrada em analytics.controle_carga."""

    ultima_carga_em: datetime | None = Field(
        default=None, description="Início da última execução registrada"
    )
    status: str | None = Field(
        default=None, description="Status da última execução (ex.: 'sucesso')"
    )
    registros_inseridos: int | None = Field(
        default=None, description="Registros inseridos na última execução"
    )
    registros_atualizados: int | None = Field(
        default=None, description="Registros atualizados na última execução"
    )
    mensagem: str | None = Field(
        default=None, description="Mensagem descritiva da última execução"
    )
