"""Testes das rotas administrativas da camada analítica.

Usam o SQLite de teste (ver tests/conftest.py), que nunca tem o schema
`analytics` (exclusivo de PostgreSQL/plpgsql). Isso é aproveitado para testar
o caminho de erro de banco sem precisar simular nada; o caminho de sucesso é
testado com `AnalyticsRepository` substituído via monkeypatch, sem depender
de um PostgreSQL real.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.api.app import app
from app.repositories.analytics_repository import (
    AnalyticsRepository,
    ResultadoRefreshAnalytics,
    StatusCargaAnalytics,
)

cliente = TestClient(app)


def test_atualizar_analytics_sem_schema_retorna_500_sem_expor_detalhes() -> None:
    resposta = cliente.post("/api/v1/analytics/atualizar")

    assert resposta.status_code == 500
    corpo = resposta.json()
    assert "não foi possível" in corpo["detail"].lower()
    assert "traceback" not in corpo["detail"].lower()
    assert "select" not in corpo["detail"].lower()


def test_status_analytics_sem_schema_retorna_500_sem_expor_detalhes() -> None:
    resposta = cliente.get("/api/v1/analytics/status")

    assert resposta.status_code == 500
    corpo = resposta.json()
    assert "não foi possível" in corpo["detail"].lower()


def test_atualizar_analytics_sucesso_retorna_contagens(monkeypatch: pytest.MonkeyPatch) -> None:
    resultado_simulado = ResultadoRefreshAnalytics(
        dimensoes_modelo_inseridas=2,
        fatos_inseridos=10,
        fatos_atualizados=1,
        executado_em=datetime(2026, 7, 18, 12, 0, 0, tzinfo=timezone.utc),
    )

    def _executar_refresh_simulado(self: AnalyticsRepository) -> ResultadoRefreshAnalytics:
        return resultado_simulado

    monkeypatch.setattr(AnalyticsRepository, "executar_refresh", _executar_refresh_simulado)

    resposta = cliente.post("/api/v1/analytics/atualizar")

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["dimensoes_modelo_inseridas"] == 2
    assert corpo["fatos_inseridos"] == 10
    assert corpo["fatos_atualizados"] == 1


def test_status_analytics_sem_execucao_anterior(monkeypatch: pytest.MonkeyPatch) -> None:
    def _obter_ultima_carga_vazia(self: AnalyticsRepository) -> None:
        return None

    monkeypatch.setattr(AnalyticsRepository, "obter_ultima_carga", _obter_ultima_carga_vazia)

    resposta = cliente.get("/api/v1/analytics/status")

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["ultima_carga_em"] is None
    assert corpo["status"] is None
    assert "nenhuma atualização" in corpo["mensagem"].lower()


def test_status_analytics_com_execucao_anterior(monkeypatch: pytest.MonkeyPatch) -> None:
    status_simulado = StatusCargaAnalytics(
        carga_id=1,
        processo="refresh_modelo_analitico",
        iniciado_em=datetime(2026, 7, 18, 10, 0, 0, tzinfo=timezone.utc),
        finalizado_em=datetime(2026, 7, 18, 10, 0, 5, tzinfo=timezone.utc),
        status="sucesso",
        registros_inseridos=5,
        registros_atualizados=0,
        mensagem="Refresh concluído: 1 modelo(s) novo(s), 5 fato(s) inserido(s), 0 atualizado(s).",
    )

    def _obter_ultima_carga_simulada(self: AnalyticsRepository) -> StatusCargaAnalytics:
        return status_simulado

    monkeypatch.setattr(AnalyticsRepository, "obter_ultima_carga", _obter_ultima_carga_simulada)

    resposta = cliente.get("/api/v1/analytics/status")

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["status"] == "sucesso"
    assert corpo["registros_inseridos"] == 5
    assert corpo["registros_atualizados"] == 0
