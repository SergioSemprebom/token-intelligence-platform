"""Gerenciamento seguro, persistência e sincronização de provedores."""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Literal

import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, SecretStr
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.provider_connection import ProviderConnection
from app.database.session import obter_sessao
from app.security.encryption import criptografar, descriptografar

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


async def _validar_chave(secret: str) -> None:
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(OPENAI_USERS_URL, headers={"Authorization": f"Bearer {secret}"}, params={"limit": 1})
    except httpx.TimeoutException as exc:
        raise ValueError("A OpenAI não respondeu dentro do tempo esperado.") from exc
    except httpx.HTTPError as exc:
        raise ValueError("Não foi possível estabelecer comunicação segura com a OpenAI.") from exc
    _validate_response(response)


async def _sincronizar(secret: str, orcamento: float) -> dict:
    now = datetime.now(timezone.utc)
    start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    common = {"start_time": int(start.timestamp()), "end_time": int(now.timestamp()), "bucket_width": "1d", "limit": 31}
    headers = {"Authorization": f"Bearer {secret}"}
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            costs_response = await client.get(OPENAI_COSTS_URL, headers=headers, params=common)
            usage_response = await client.get(OPENAI_USAGE_URL, headers=headers, params={**common, "group_by": "model"})
    except httpx.TimeoutException as exc:
        raise ValueError("A sincronização excedeu o tempo esperado.") from exc
    except httpx.HTTPError as exc:
        raise ValueError("Falha de comunicação durante a sincronização.") from exc
    _validate_response(costs_response); _validate_response(usage_response)

    gasto_total = 0.0; consumo_diario = []
    for bucket in costs_response.json().get("data", []):
        day_total = sum(float((item.get("amount") or {}).get("value", 0) or 0) for item in bucket.get("results", []))
        gasto_total += day_total
        consumo_diario.append({"dia": datetime.fromtimestamp(bucket.get("start_time", int(start.timestamp())), timezone.utc).strftime("%d"), "custo": round(day_total, 6)})

    input_tokens = output_tokens = requests = 0; modelos = {}
    for bucket in usage_response.json().get("data", []):
        for item in bucket.get("results", []):
            inp = int(item.get("input_tokens", 0) or 0); out = int(item.get("output_tokens", 0) or 0); req = int(item.get("num_model_requests", 0) or 0)
            input_tokens += inp; output_tokens += out; requests += req
            model = item.get("model") or "não identificado"
            row = modelos.setdefault(model, {"modelo": model, "tokens": 0, "requisicoes": 0})
            row["tokens"] += inp + out; row["requisicoes"] += req

    days_month = 31 if now.month in {1,3,5,7,8,10,12} else 30 if now.month != 2 else (29 if now.year % 4 == 0 else 28)
    projection = gasto_total / max(now.day, 1) * days_month
    return {
        "periodo": now.strftime("%Y-%m"), "moeda": "USD", "origem_dados": "openai_real",
        "ultima_sincronizacao": now.isoformat(), "gasto_mes": round(gasto_total, 6),
        "orcamento_mensal": orcamento, "projecao_mes": round(projection, 6),
        "tokens_total": input_tokens + output_tokens, "tokens_entrada": input_tokens,
        "tokens_saida": output_tokens, "requisicoes_total": requests, "economia_estimada": 0.0,
        "consumo_diario": consumo_diario,
        "provedores": [{"nome": "OpenAI", "slug": "openai", "status": "dados_reais", "tokens": input_tokens + output_tokens, "requisicoes": requests, "custo": round(gasto_total, 6)}],
        "modelos": sorted(modelos.values(), key=lambda x: x["tokens"], reverse=True),
    }


@router.get("", summary="Lista provedores e disponibilidade")
def listar_provedores() -> list[dict[str, str]]:
    return [
        {"nome": "OpenAI", "slug": "openai", "status": "persistencia_disponivel", "tipo_credencial": "Admin API Key"},
        {"nome": "Gemini", "slug": "gemini", "status": "planejado", "tipo_credencial": "Google Cloud"},
        {"nome": "Claude", "slug": "anthropic", "status": "planejado", "tipo_credencial": "Admin API Key"},
        {"nome": "OpenRouter", "slug": "openrouter", "status": "planejado", "tipo_credencial": "Management Key"},
    ]


@router.post("/openai/testar", summary="Testa conexão simulada ou real com OpenAI")
async def testar_openai(payload: OpenAIConnectionRequest) -> dict:
    secret = _secret(payload)
    if payload.modo_simulacao:
        return {"provedor": "openai", "nome": payload.nome, "status": "simulado", "credencial_mascarada": _mask_secret(secret), "orcamento_mensal": payload.orcamento_mensal, "moeda": payload.moeda, "mensagem": "Conexão simulada validada. Nenhuma chamada externa foi realizada."}
    if not secret:
        raise ValueError("Informe uma Admin API Key da OpenAI.")
    await _validar_chave(secret)
    return {"provedor": "openai", "nome": payload.nome, "status": "conectado", "credencial_mascarada": _mask_secret(secret), "orcamento_mensal": payload.orcamento_mensal, "moeda": payload.moeda, "mensagem": "Credencial administrativa validada com sucesso na OpenAI."}


@router.post("/openai/salvar", summary="Valida e salva a conexão OpenAI criptografada")
async def salvar_openai(payload: OpenAIConnectionRequest, sessao: Session = Depends(obter_sessao)) -> dict:
    secret = _secret(payload)
    if payload.modo_simulacao or not secret:
        raise ValueError("Para salvar, desative a simulação e informe uma Admin API Key.")
    await _validar_chave(secret)
    existente = sessao.scalar(select(ProviderConnection).where(ProviderConnection.provider_slug == "openai", ProviderConnection.ativo.is_(True)))
    if existente:
        existente.nome = payload.nome; existente.encrypted_api_key = criptografar(secret); existente.credential_hint = _mask_secret(secret)
        existente.orcamento_mensal = payload.orcamento_mensal; existente.moeda = payload.moeda; existente.ultimo_status = "conectado"; existente.ultimo_erro = None
        conexao = existente
    else:
        conexao = ProviderConnection(provider_slug="openai", nome=payload.nome, encrypted_api_key=criptografar(secret), credential_hint=_mask_secret(secret), orcamento_mensal=payload.orcamento_mensal, moeda=payload.moeda, ativo=True, ultimo_status="conectado")
        sessao.add(conexao)
    sessao.commit(); sessao.refresh(conexao)
    return {"id": str(conexao.id), "provedor": "openai", "nome": conexao.nome, "status": conexao.ultimo_status, "credencial_mascarada": conexao.credential_hint, "mensagem": "Conexão salva com criptografia no PostgreSQL."}


@router.get("/connections", summary="Lista conexões salvas sem expor credenciais")
def listar_conexoes(sessao: Session = Depends(obter_sessao)) -> list[dict]:
    rows = sessao.scalars(select(ProviderConnection).where(ProviderConnection.ativo.is_(True))).all()
    return [{"id": str(row.id), "provedor": row.provider_slug, "nome": row.nome, "credencial_mascarada": row.credential_hint, "orcamento_mensal": float(row.orcamento_mensal), "moeda": row.moeda, "status": row.ultimo_status, "ultima_sincronizacao": row.ultima_sincronizacao_em.isoformat() if row.ultima_sincronizacao_em else None} for row in rows]


@router.post("/connections/{connection_id}/sync", summary="Sincroniza usando a credencial criptografada salva")
async def sincronizar_conexao(connection_id: uuid.UUID, sessao: Session = Depends(obter_sessao)) -> dict:
    conexao = sessao.get(ProviderConnection, connection_id)
    if not conexao or not conexao.ativo:
        raise ValueError("Conexão não encontrada ou inativa.")
    try:
        result = await _sincronizar(descriptografar(conexao.encrypted_api_key), float(conexao.orcamento_mensal))
        conexao.ultima_sincronizacao_em = datetime.now(timezone.utc); conexao.ultimo_status = "sincronizado"; conexao.ultimo_erro = None
        sessao.commit()
        return result
    except Exception as exc:
        conexao.ultimo_status = "erro"; conexao.ultimo_erro = str(exc); sessao.commit()
        raise


@router.post("/openai/sincronizar", summary="Sincroniza com chave enviada sem persistir")
async def sincronizar_openai(payload: OpenAIConnectionRequest) -> dict:
    secret = _secret(payload)
    if payload.modo_simulacao or not secret:
        raise ValueError("Desative a simulação e informe uma Admin API Key.")
    return await _sincronizar(secret, payload.orcamento_mensal)
