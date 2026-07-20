"""Testes dos endpoints do dashboard da Fase 8."""


def test_dashboard_resumo(client):
    response = client.get("/api/v1/dashboard/resumo")

    assert response.status_code == 200
    body = response.json()
    assert body["moeda"] == "USD"
    assert body["orcamento_mensal"] > 0
    assert body["tokens_total"] >= 0
    assert len(body["provedores"]) == 4
    assert body["provedores"][0]["slug"] == "openai"


def test_dashboard_lista_provedores(client):
    response = client.get("/api/v1/dashboard/provedores")

    assert response.status_code == 200
    body = response.json()
    assert [item["slug"] for item in body] == [
        "openai",
        "gemini",
        "anthropic",
        "openrouter",
    ]
