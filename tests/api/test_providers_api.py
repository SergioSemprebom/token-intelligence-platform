"""Testes dos endpoints de provedores da Fase 8.1."""


def test_listar_provedores(client):
    response = client.get("/api/v1/providers")
    assert response.status_code == 200
    assert response.json()[0]["slug"] == "openai"


def test_conexao_openai_simulada_nao_expoe_chave(client):
    response = client.post(
        "/api/v1/providers/openai/testar",
        json={
            "nome": "Minha OpenAI",
            "api_key": "sk-admin-chave-super-secreta",
            "orcamento_mensal": 100,
            "moeda": "USD",
            "modo_simulacao": True,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "simulado"
    assert "chave-super-secreta" not in str(body)
    assert "••••" in body["credencial_mascarada"]


def test_conexao_real_sem_chave_retorna_422(client, monkeypatch):
    monkeypatch.delenv("OPENAI_ADMIN_API_KEY", raising=False)
    response = client.post(
        "/api/v1/providers/openai/testar",
        json={
            "nome": "Minha OpenAI",
            "orcamento_mensal": 100,
            "moeda": "USD",
            "modo_simulacao": False,
        },
    )
    assert response.status_code == 422
