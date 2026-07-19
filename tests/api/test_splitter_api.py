"""Testes da rota de divisão de texto por tokens."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.app import app

cliente = TestClient(app)

URL = "/api/v1/tokens/dividir"


def test_divisao_valida_retorna_blocos_esperados() -> None:
    texto = "palavra " * 300
    resposta = cliente.post(
        URL,
        json={
            "texto": texto,
            "modelo": "gpt-4o",
            "limite_tokens": 100,
            "sobreposicao_tokens": 10,
        },
    )

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["modelo"] == "gpt-4o"
    assert corpo["total_blocos"] == len(corpo["blocos"])
    assert corpo["total_blocos"] >= 2
    assert corpo["total_tokens_original"] > 0

    primeiro_bloco = corpo["blocos"][0]
    assert primeiro_bloco["indice"] == 0
    assert primeiro_bloco["quantidade_tokens"] == 100
    assert primeiro_bloco["token_inicial"] == 0
    assert primeiro_bloco["token_final"] == 99


def test_divisao_com_limite_invalido_retorna_422() -> None:
    resposta = cliente.post(
        URL,
        json={"texto": "algum texto", "limite_tokens": 0},
    )

    assert resposta.status_code == 422


def test_divisao_com_sobreposicao_invalida_retorna_422() -> None:
    resposta = cliente.post(
        URL,
        json={
            "texto": "algum texto com varias palavras",
            "limite_tokens": 5,
            "sobreposicao_tokens": 5,
        },
    )

    assert resposta.status_code == 422
    assert "sobreposição" in resposta.text.lower()


def test_divisao_com_texto_vazio_retorna_422() -> None:
    resposta = cliente.post(
        URL,
        json={"texto": "   ", "limite_tokens": 10},
    )

    assert resposta.status_code == 422
