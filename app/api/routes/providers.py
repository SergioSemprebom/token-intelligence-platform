"""Gerenciamento de provedores e sincronização real da OpenAI."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Literal

import httpx
from fastapi import APIRouter
from pydantic import BaseModel, Field, SecretStr

router = APIRouter(prefix="/api/v1/providers", tags=["Provedores"])
OPENAI_USERS_URL = "https://api.openai.com/v1/organization/users"
OPENAI_COSTS_URL = "https://api.openai.com/v1/organization/costs"
OPENAI_USAGE_URL = "https://api.openai.com/v1/organization/usage/completions"


class OpenAIConnectionRequest(BaseModel):
    nome: str = Field(min_length=3, max_length=80)
    api_key: SecretStr | None = None
    orcamento_mensal: float = Field(default=100.0, gt=0)
    moeda: Literal["USD", "BRL"] = "USD"
    modo_simulacao: bool = True


class ProviderConnectionResponse(BaseModel):
    provedor: str
    nome: str
    status: str
    credencial_mascarada: str
    orcamento_mensal: float
    moeda: str
    mensagem: str


def _mask_secret(value: str | None) -> str:
    if not value:
        return "não informada"
    if len(value) <= 8:
        return "••••••••"
    return f"{value[:5]}••••••••{value[-4:]}"


def _secret(payload: OpenAIConnectionRequest) -> str | None:
    supplied = payload.api_key.get_secret_value() if payload.api_key else None
    return supplied or os.getenv("OPENAI_ADMIN_API_KEY")


def _validate_response(response: httpx.Response) -> None:
    if response.status_code in {401, 403}:
        raise ValueError("Chave administrativa inválida ou sem permissão de proprietário da organização.")
    if response.status_code >= 400:
        raise ValueError(f"A OpenAI recusou a solicitação (HTTP {response.status_code}).")


@router.get("", summary="Lista provedores e disponibilidade")
def listar_provedores() -> list[dict[str, str]]:
    return [
        {"nome": "OpenAI", "slug": "openai", "status": "sincronizacao_real_disponivel", "tipo_credencial": "Admin API Key"},
        {"nome": "Gemini", "slug": "gemini", "status": "planejado", "tipo_credencial": "Google Cloud"},
        {"nome": "Claude", "slug": "anthropic", "status": "planejado", "tipo_credencial": "Admin API Key"},
        {"nome": "OpenRouter", "slug": "openrouter", "status": "planejado", "tipo_credencial": "Management Key"},
    ]


@router.post("/openai/testar", response_model=ProviderConnectionResponse, summary="Testa conexão simulada ou real com OpenAI")
async def testar_openai(payload: OpenAIConnectionRequest) -> ProviderConnectionResponse:
    secret = _secret(payload)
    if payload.modo_simulacao:
        return ProviderConnectionResponse(provedor="openai", nome=payload.nome, status="simulado", credencial_mascarada=_mask_secret(secret), orcamento_mensal=payload.orcamento_mensal, moeda=payload.moeda, mensagem="Conexão simulada validada. Nenhuma chamada externa foi realizada.")
    if not secret:
        raise ValueError("Informe uma Admin API Key da OpenAI ou configure OPENAI_ADMIN_API_KEY no arquivo .env.")
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(OPENAI_USERS_URL, headers={"Authorization": f"Bearer {secret}"}, params={"limit": 1})
    except httpx.TimeoutException as exc:
        raise ValueError("A OpenAI não respondeu dentro do tempo esperado.") from exc
    except httpx.HTTPError as exc:
        raise ValueError("Não foi possível estabelecer comunicação segura com a OpenAI.") from exc
    _validate_response(response)
    return ProviderConnectionResponse(provedor="openai", nome=payload.nome, status="conectado", credencial_mascarada=_mask_secret(secret), orcamento_mensal=payload.orcamento_mensal, moeda=payload.moeda, mensagem="Credencial administrativa validada com sucesso na OpenAI.")


@router.post("/openai/sincronizar", summary="Busca custos, tokens e requisições reais do mês")
async def sincronizar_openai(payload: OpenAIConnectionRequest) -> dict:
    secret = _secret(payload)
    if payload.modo_simulacao:
        raise ValueError("Desative o modo de simulação para carregar dados reais.")
    if not secret:
        raise ValueError("Informe uma Admin API Key da OpenAI.")

    now = datetime.now(timezone.utc)
    start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    start_ts, end_ts = int(start.timestamp()), int(now.timestamp())
    headers = {"Authorization": f"Bearer {secret}"}
    common = {"start_time": start_ts, "end_time": end_ts, "bucket_width": "1d", "limit": 31}
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            costs_response, usage_response = await client.get(OPENAI_COSTS_URL, headers=headers, params=common), await client.get(OPENAI_USAGE_URL, headers=headers, params={**common, "group_by": "model"})
    except httpx.TimeoutException as exc:
        raise ValueError("A sincronização excedeu o tempo esperado.") from exc
    except httpx.HTTPError as exc:
        raise ValueError("Falha de comunicação durante a sincronização.") from exc
    _validate_response(costs_response)
    _validate_response(usage_response)

    costs_json, usage_json = costs_response.json(), usage_response.json()
    gasto_total = 0.0
    consumo_diario: list[dict] = []
    for bucket in costs_json.get("data", []):
        day_total = 0.0
        for item in bucket.get("results", []):
            amount = item.get("amount", {})
            day_total += float(amount.get("value", 0) or 0)
        gasto_total += day_total
        consumo_diario.append({"dia": datetime.fromtimestamp(bucket.get("start_time", start_ts), timezone.utc).strftime("%d"), "custo": round(day_total, 6)})

    input_tokens = output_tokens = requests = 0
    modelos: dict[str, dict] = {}
    for bucket in usage_json.get("data", []):
        for item in bucket.get("results", []):
            inp = int(item.get("input_tokens", 0) or 0)
            out = int(item.get("output_tokens", 0) or 0)
            req = int(item.get("num_model_requests", 0) or 0)
            input_tokens += inp; output_tokens += out; requests += req
            model = item.get("model") or "não identificado"
            row = modelos.setdefault(model, {"modelo": model, "tokens": 0, "requisicoes": 0})
            row["tokens"] += inp + out; row["requisicoes"] += req

    elapsed_days = max(now.day, 1)
    days_month = 31 if now.month in {1,3,5,7,8,10,12} else 30 if now.month != 2 else (29 if now.year % 4 == 0 else 28)
    projection = gasto_total / elapsed_days * days_month
    return {
        "periodo": now.strftime("%Y-%m"), "moeda": "USD", "origem_dados": "openai_real",
        "ultima_sincronizacao": now.isoformat(), "gasto_mes": round(gasto_total, 6),
        "orcamento_mensal": payload.orcamento_mensal, "projecao_mes": round(projection, 6),
        "tokens_total": input_tokens + output_tokens, "tokens_entrada": input_tokens,
        "tokens_saida": output_tokens, "requisicoes_total": requests, "economia_estimada": 0.0,
        "consumo_diario": consumo_diario,
        "provedores": [{"nome": "OpenAI", "slug": "openai", "status": "dados_reais", "tokens": input_tokens + output_tokens, "requisicoes": requests, "custo": round(gasto_total, 6)}],
        "modelos": sorted(modelos.values(), key=lambda x: x["tokens"], reverse=True),
    }
