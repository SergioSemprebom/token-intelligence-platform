"""Testes das rotas raiz e de saúde da API."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.app import app

cliente = TestClient(app)


def test_rota_raiz_retorna_informacoes_da_api() -> None:
    resposta = cliente.get("/")

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["aplicacao"] == "Token Intelligence Platform API"
    assert corpo["versao"] == "0.7.0"
    assert corpo["documentacao"] == "/docs"


def test_rota_saude_retorna_status_ok() -> None:
    resposta = cliente.get("/health")

    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok"}
