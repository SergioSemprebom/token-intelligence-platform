"""Testes da rota de comparação de tokenização entre modelos."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.app import app

cliente = TestClient(app)

URL = "/api/v1/tokens/comparar-modelos"


def test_comparacao_valida_retorna_um_resultado_por_modelo() -> None:
    resposta = cliente.post(
        URL,
        json={"texto": "Texto para comparar", "modelos": ["gpt-4o", "gpt-4"]},
    )

    assert resposta.status_code == 200
    resultados = resposta.json()["resultados"]
    assert len(resultados) == 2
    assert resultados[0]["modelo_solicitado"] == "gpt-4o"
    assert resultados[0]["fallback_utilizado"] is False
    assert resultados[0]["aviso"] is None


def test_comparacao_com_modelo_desconhecido_indica_fallback_sem_ocultar() -> None:
    resposta = cliente.post(
        URL,
        json={"texto": "Texto para comparar", "modelos": ["modelo-inexistente"]},
    )

    assert resposta.status_code == 200
    resultado = resposta.json()["resultados"][0]
    assert resultado["fallback_utilizado"] is True
    assert resultado["encoding_utilizado"] == "o200k_base"
    assert resultado["aviso"] is not None


def test_comparacao_com_lista_de_modelos_vazia_retorna_422() -> None:
    resposta = cliente.post(URL, json={"texto": "Texto", "modelos": []})

    assert resposta.status_code == 422


def test_comparacao_com_texto_vazio_retorna_422() -> None:
    resposta = cliente.post(URL, json={"texto": "   ", "modelos": ["gpt-4o"]})

    assert resposta.status_code == 422
