"""Testes da rota de estimativa de custo."""

from __future__ import annotations

from decimal import Decimal

from fastapi.testclient import TestClient

from app.api.app import app

cliente = TestClient(app)

URL = "/api/v1/custos/estimar"


def test_estimativa_valida_retorna_valores_como_string() -> None:
    resposta = cliente.post(
        URL,
        json={"modelo": "gpt-4o", "tokens_entrada": 115, "tokens_saida": 100},
    )

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["modelo"] == "gpt-4o"
    assert corpo["tokens_entrada"] == 115
    assert corpo["tokens_saida"] == 100
    assert corpo["total_tokens"] == 215
    assert isinstance(corpo["custo_entrada"], str)
    assert isinstance(corpo["custo_saida"], str)
    assert isinstance(corpo["custo_total"], str)
    assert Decimal(corpo["custo_total"]) == Decimal(corpo["custo_entrada"]) + Decimal(
        corpo["custo_saida"]
    )
    assert corpo["moeda"] == "USD"
    assert corpo["aviso"]


def test_estimativa_com_modelo_inexistente_retorna_erro_claro() -> None:
    resposta = cliente.post(
        URL,
        json={"modelo": "modelo-que-nao-existe", "tokens_entrada": 10, "tokens_saida": 10},
    )

    assert resposta.status_code in (404, 422)
    assert "não encontrado" in resposta.text.lower()


def test_estimativa_com_tokens_negativos_retorna_422() -> None:
    resposta = cliente.post(
        URL,
        json={"modelo": "gpt-4o", "tokens_entrada": -1, "tokens_saida": 10},
    )

    assert resposta.status_code == 422
