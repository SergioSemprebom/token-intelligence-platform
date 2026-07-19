"""Testes da rota de análise de texto."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.app import app

cliente = TestClient(app)

URL = "/api/v1/tokens/analisar"


def test_analise_valida_retorna_metricas_esperadas() -> None:
    resposta = cliente.post(URL, json={"texto": "Texto para analisar", "modelo": "gpt-4o"})

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["modelo"] == "gpt-4o"
    assert corpo["encoding"] == "o200k_base"
    assert corpo["caracteres"] == len("Texto para analisar")
    assert corpo["palavras"] == 3
    assert corpo["tokens"] > 0
    assert corpo["bytes_utf8"] > 0
    assert corpo["media_caracteres_por_token"] > 0
    assert corpo["tempo_processamento_ms"] >= 0
    assert corpo["fallback_utilizado"] is False
    assert "token_ids" not in corpo or corpo["token_ids"] is None


def test_analise_com_texto_vazio_retorna_422_com_mensagem_clara() -> None:
    resposta = cliente.post(URL, json={"texto": "   "})

    assert resposta.status_code == 422
    assert "não pode estar vazio" in resposta.text


def test_analise_sem_texto_no_corpo_retorna_422() -> None:
    resposta = cliente.post(URL, json={"modelo": "gpt-4o"})

    assert resposta.status_code == 422


def test_analise_com_token_ids_inclui_lista_na_resposta() -> None:
    resposta = cliente.post(
        URL,
        json={"texto": "Ola mundo", "modelo": "gpt-4o", "incluir_token_ids": True},
    )

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert isinstance(corpo["token_ids"], list)
    assert len(corpo["token_ids"]) == corpo["tokens"]


def test_analise_sem_solicitar_token_ids_nao_inclui_lista() -> None:
    resposta = cliente.post(
        URL,
        json={"texto": "Ola mundo", "modelo": "gpt-4o", "incluir_token_ids": False},
    )

    assert resposta.status_code == 200
    assert resposta.json()["token_ids"] is None


def test_analise_com_modelo_desconhecido_indica_fallback() -> None:
    resposta = cliente.post(URL, json={"texto": "Ola mundo", "modelo": "modelo-inexistente"})

    assert resposta.status_code == 200
    assert resposta.json()["fallback_utilizado"] is True


def test_resposta_de_erro_nao_expoe_stack_trace() -> None:
    resposta = cliente.post(URL, json={"texto": "   "})

    corpo = resposta.json()
    assert "traceback" not in resposta.text.lower()
    assert list(corpo.keys()) == ["detail"]
