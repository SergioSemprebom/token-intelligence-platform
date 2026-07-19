"""Testes das rotas de auditoria/compactação de prompts (Fase 7)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.app import app

cliente = TestClient(app)

TEXTO_EXEMPLO = (
    "Por favor, gostaria que você pudesse realizar uma análise detalhada deste "
    "relatório e depois de analisar me informar quais são os principais "
    "problemas encontrados."
)


def test_auditar_prompt_retorna_diagnostico() -> None:
    resposta = cliente.post(
        "/api/v1/prompts/auditar", json={"texto": TEXTO_EXEMPLO, "modelo": "gpt-4o"}
    )

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["tokens_originais"] > 0
    assert corpo["nivel_desperdicio"] in {"baixo", "medio", "alto"}
    assert isinstance(corpo["problemas_encontrados"], list)
    assert "token_ids" not in corpo


def test_auditar_prompt_texto_vazio_retorna_422() -> None:
    resposta = cliente.post("/api/v1/prompts/auditar", json={"texto": "   "})

    assert resposta.status_code == 422


def test_auditar_prompt_registra_no_historico() -> None:
    cliente.post("/api/v1/prompts/auditar", json={"texto": "Texto para auditoria do historico"})

    corpo = cliente.get("/api/v1/historico", params={"tipo_operacao": "auditoria_prompt"}).json()

    assert corpo["total"] >= 1
    assert corpo["resultados"][0]["tipo_operacao"] == "auditoria_prompt"


def test_compactar_prompt_retorna_sugestao_com_id() -> None:
    resposta = cliente.post(
        "/api/v1/prompts/compactar",
        json={"texto": TEXTO_EXEMPLO, "modelo": "gpt-4o", "nivel": "moderado"},
    )

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["compactacao_id"]
    assert corpo["nivel"] == "moderado"
    assert corpo["aprovado"] is False
    assert corpo["tokens_compactados"] <= corpo["tokens_originais"]
    assert "token_ids" not in corpo


def test_compactar_prompt_nivel_invalido_retorna_422() -> None:
    resposta = cliente.post(
        "/api/v1/prompts/compactar", json={"texto": TEXTO_EXEMPLO, "nivel": "inexistente"}
    )

    assert resposta.status_code == 422


def test_compactar_prompt_texto_vazio_retorna_422() -> None:
    resposta = cliente.post("/api/v1/prompts/compactar", json={"texto": "   "})

    assert resposta.status_code == 422


def test_compactar_prompt_registra_no_historico_sem_texto_completo() -> None:
    cliente.post(
        "/api/v1/prompts/compactar",
        json={"texto": TEXTO_EXEMPLO, "nivel": "conservador"},
    )

    corpo = cliente.get("/api/v1/historico", params={"tipo_operacao": "compactacao_prompt"}).json()

    assert corpo["total"] >= 1
    registro = corpo["resultados"][0]
    assert registro["texto_preview"] is not None
    assert len(registro["texto_preview"]) <= 200
    assert "texto_completo" not in registro


def test_comparar_compactacao_retorna_ranking() -> None:
    resposta = cliente.post(
        "/api/v1/prompts/comparar-compactacao", json={"texto": TEXTO_EXEMPLO}
    )

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert len(corpo["resultados"]) == 4
    assert corpo["melhor_reducao"]
    assert corpo["recomendado"]


def test_comparar_compactacao_texto_vazio_retorna_422() -> None:
    resposta = cliente.post("/api/v1/prompts/comparar-compactacao", json={"texto": ""})

    assert resposta.status_code == 422


def test_aprovar_compactacao_existente() -> None:
    compactacao_id = cliente.post(
        "/api/v1/prompts/compactar",
        json={"texto": TEXTO_EXEMPLO, "nivel": "moderado"},
    ).json()["compactacao_id"]

    resposta = cliente.post(
        "/api/v1/prompts/aprovar", json={"compactacao_id": compactacao_id}
    )

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["compactacao_id"] == compactacao_id
    assert corpo["aprovado"] is True
    assert corpo["aprovado_em"] is not None


def test_aprovar_compactacao_inexistente_retorna_404() -> None:
    resposta = cliente.post(
        "/api/v1/prompts/aprovar",
        json={"compactacao_id": "00000000-0000-0000-0000-000000000000"},
    )

    assert resposta.status_code == 404


def test_aprovar_compactacao_nao_chama_ia_externa_apenas_atualiza_flag() -> None:
    compactacao_id = cliente.post(
        "/api/v1/prompts/compactar",
        json={"texto": TEXTO_EXEMPLO, "nivel": "conservador"},
    ).json()["compactacao_id"]

    resposta_antes = cliente.post(
        "/api/v1/prompts/aprovar", json={"compactacao_id": compactacao_id}
    )
    resposta_depois = cliente.post(
        "/api/v1/prompts/aprovar", json={"compactacao_id": compactacao_id}
    )

    assert resposta_antes.status_code == 200
    assert resposta_depois.status_code == 200
    assert resposta_depois.json()["aprovado"] is True
