"""Testes das rotas de histórico de processamentos."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.api.app import app
from app.repositories.processamento_repository import ProcessamentoRepository

cliente = TestClient(app)


def test_listar_historico_vazio_retorna_paginacao_zerada() -> None:
    resposta = cliente.get("/api/v1/historico")

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["total"] == 0
    assert corpo["limite"] == 20
    assert corpo["offset"] == 0
    assert corpo["resultados"] == []


def test_analisar_texto_registra_no_historico() -> None:
    resposta_analise = cliente.post(
        "/api/v1/tokens/analisar", json={"texto": "Texto para o histórico", "modelo": "gpt-4o"}
    )
    assert resposta_analise.status_code == 200

    corpo = cliente.get("/api/v1/historico").json()

    assert corpo["total"] == 1
    assert corpo["resultados"][0]["tipo_operacao"] == "analise"
    assert corpo["resultados"][0]["modelo_solicitado"] == "gpt-4o"
    assert "token_ids" not in corpo["resultados"][0]


def test_filtro_por_tipo_operacao() -> None:
    cliente.post("/api/v1/tokens/analisar", json={"texto": "Analisar", "modelo": "gpt-4o"})
    cliente.post(
        "/api/v1/tokens/dividir",
        json={"texto": "Texto " * 100, "modelo": "gpt-4o", "limite_tokens": 20},
    )

    resposta = cliente.get("/api/v1/historico", params={"tipo_operacao": "divisao"})
    corpo = resposta.json()

    assert corpo["total"] == 1
    assert corpo["resultados"][0]["tipo_operacao"] == "divisao"


def test_tipo_operacao_invalido_retorna_422() -> None:
    resposta = cliente.get("/api/v1/historico", params={"tipo_operacao": "invalido"})

    assert resposta.status_code == 422


def test_data_inicio_posterior_a_data_fim_retorna_422() -> None:
    resposta = cliente.get(
        "/api/v1/historico",
        params={"data_inicio": "2026-07-18T12:00:00Z", "data_fim": "2026-07-01T00:00:00Z"},
    )

    assert resposta.status_code == 422


def test_buscar_processamento_por_id_existente() -> None:
    cliente.post("/api/v1/tokens/analisar", json={"texto": "Buscar depois", "modelo": "gpt-4o"})
    processamento_id = cliente.get("/api/v1/historico").json()["resultados"][0]["id"]

    resposta = cliente.get(f"/api/v1/historico/{processamento_id}")

    assert resposta.status_code == 200
    assert resposta.json()["id"] == processamento_id


def test_buscar_processamento_inexistente_retorna_404() -> None:
    resposta = cliente.get("/api/v1/historico/00000000-0000-0000-0000-000000000000")

    assert resposta.status_code == 404


def test_resumo_agrega_totais() -> None:
    cliente.post("/api/v1/tokens/analisar", json={"texto": "Resumo 1", "modelo": "gpt-4o"})
    cliente.post(
        "/api/v1/custos/estimar",
        json={"modelo": "gpt-4o", "tokens_entrada": 100, "tokens_saida": 50},
    )

    resposta = cliente.get("/api/v1/historico/resumo")
    corpo = resposta.json()

    assert resposta.status_code == 200
    assert corpo["total_processamentos"] == 2
    assert isinstance(corpo["custo_total"], str)
    assert corpo["processamentos_por_tipo"]["analise"] == 1
    assert corpo["processamentos_por_tipo"]["estimativa_custo"] == 1


def test_endpoint_analisar_funciona_mesmo_com_falha_no_historico(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _criar_com_falha(self: ProcessamentoRepository, processamento: object) -> None:
        raise SQLAlchemyError("falha simulada de conexão com o banco")

    monkeypatch.setattr(ProcessamentoRepository, "criar", _criar_com_falha)

    resposta = cliente.post(
        "/api/v1/tokens/analisar",
        json={"texto": "Deve funcionar mesmo assim", "modelo": "gpt-4o"},
    )

    assert resposta.status_code == 200
    assert resposta.json()["tokens"] > 0
