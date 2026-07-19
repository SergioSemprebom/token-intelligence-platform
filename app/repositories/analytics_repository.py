"""Acesso à camada analítica (schema `analytics`), sem regra de negócio."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class ResultadoRefreshAnalytics:
    """Resultado de uma execução de `analytics.refresh_modelo_analitico()`."""

    dimensoes_modelo_inseridas: int
    fatos_inseridos: int
    fatos_atualizados: int
    executado_em: datetime


@dataclass(frozen=True)
class ResultadoRefreshCompactacoes:
    """Resultado de uma execução de `analytics.refresh_compactacoes_prompt()`."""

    dimensoes_modelo_inseridas: int
    fatos_inseridos: int
    fatos_atualizados: int
    executado_em: datetime


@dataclass(frozen=True)
class StatusCargaAnalytics:
    """Registro de execução lido de `analytics.controle_carga`."""

    carga_id: int
    processo: str
    iniciado_em: datetime
    finalizado_em: datetime | None
    status: str
    registros_inseridos: int
    registros_atualizados: int
    mensagem: str | None


class AnalyticsRepository:
    """Executa a carga incremental da camada analítica e consulta seu status."""

    def __init__(self, sessao: Session) -> None:
        self._sessao = sessao

    def executar_refresh(self) -> ResultadoRefreshAnalytics:
        """Executa `analytics.refresh_modelo_analitico()` e retorna o resultado."""
        try:
            linha = self._sessao.execute(
                text("SELECT * FROM analytics.refresh_modelo_analitico()")
            ).one()
            self._sessao.commit()
        except SQLAlchemyError:
            self._sessao.rollback()
            raise

        return ResultadoRefreshAnalytics(
            dimensoes_modelo_inseridas=linha.dimensoes_modelo_inseridas,
            fatos_inseridos=linha.fatos_inseridos,
            fatos_atualizados=linha.fatos_atualizados,
            executado_em=linha.executado_em,
        )

    def executar_refresh_compactacoes(self) -> ResultadoRefreshCompactacoes:
        """Executa `analytics.refresh_compactacoes_prompt()` e retorna o resultado.

        Função separada de `executar_refresh()` (que roda
        `refresh_modelo_analitico()`), para não alterar seu comportamento nem
        sua assinatura já usados em produção.
        """
        try:
            linha = self._sessao.execute(
                text("SELECT * FROM analytics.refresh_compactacoes_prompt()")
            ).one()
            self._sessao.commit()
        except SQLAlchemyError:
            self._sessao.rollback()
            raise

        return ResultadoRefreshCompactacoes(
            dimensoes_modelo_inseridas=linha.dimensoes_modelo_inseridas,
            fatos_inseridos=linha.fatos_inseridos,
            fatos_atualizados=linha.fatos_atualizados,
            executado_em=linha.executado_em,
        )

    def obter_ultima_carga(self, processo: str | None = None) -> StatusCargaAnalytics | None:
        """Retorna a execução mais recente registrada em `analytics.controle_carga`.

        Quando `processo` é informado, filtra pelo nome do processo (ex.:
        'refresh_compactacoes_prompt'); por padrão (None) retorna a mais
        recente entre todos os processos, preservando o comportamento anterior.
        """
        condicao_processo = " WHERE processo = :processo" if processo else ""
        linha = self._sessao.execute(
            text(
                "SELECT carga_id, processo, iniciado_em, finalizado_em, status, "
                "registros_inseridos, registros_atualizados, mensagem "
                "FROM analytics.controle_carga"
                f"{condicao_processo} "
                "ORDER BY iniciado_em DESC "
                "LIMIT 1"
            ),
            {"processo": processo} if processo else {},
        ).one_or_none()

        if linha is None:
            return None

        return StatusCargaAnalytics(
            carga_id=linha.carga_id,
            processo=linha.processo,
            iniciado_em=linha.iniciado_em,
            finalizado_em=linha.finalizado_em,
            status=linha.status,
            registros_inseridos=linha.registros_inseridos,
            registros_atualizados=linha.registros_atualizados,
            mensagem=linha.mensagem,
        )
