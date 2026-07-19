"""Schemas de saída do histórico de processamentos."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator


def _decimal_para_string(valor: Any) -> Any:
    """Converte valores Decimal para string, preservando precisão no JSON."""
    if isinstance(valor, Decimal):
        return str(valor)
    return valor


class ProcessamentoResponse(BaseModel):
    """Representação pública de um registro do histórico de processamentos."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    criado_em: datetime
    tipo_operacao: str
    origem: str
    modelo_solicitado: str | None = None
    encoding_utilizado: str | None = None
    fallback_utilizado: bool
    caracteres: int | None = None
    palavras: int | None = None
    bytes_utf8: int | None = None
    tokens_entrada: int
    tokens_saida: int
    total_tokens: int
    quantidade_blocos: int | None = None
    limite_tokens_bloco: int | None = None
    sobreposicao_tokens: int | None = None
    custo_entrada: str | None = None
    custo_saida: str | None = None
    custo_total: str | None = None
    moeda: str | None = None
    tempo_processamento_ms: str | None = None
    texto_hash: str | None = None
    texto_preview: str | None = None
    sucesso: bool
    mensagem_erro: str | None = None
    metadados: dict[str, Any] | None = None

    @field_validator(
        "custo_entrada",
        "custo_saida",
        "custo_total",
        "tempo_processamento_ms",
        mode="before",
    )
    @classmethod
    def _converter_decimais(cls, valor: Any) -> Any:
        return _decimal_para_string(valor)


class HistoricoPaginadoResponse(BaseModel):
    """Resposta paginada da listagem do histórico de processamentos."""

    total: int
    limite: int
    offset: int
    resultados: list[ProcessamentoResponse]


class HistoricoResumoResponse(BaseModel):
    """Resumo agregado do histórico de processamentos."""

    total_processamentos: int
    total_tokens_entrada: int
    total_tokens_saida: int
    total_tokens: int
    custo_total: str
    quantidade_sucessos: int
    quantidade_erros: int
    processamentos_por_tipo: dict[str, int]
    processamentos_por_modelo: dict[str, int]

    @field_validator("custo_total", mode="before")
    @classmethod
    def _converter_custo_total(cls, valor: Any) -> Any:
        return _decimal_para_string(valor)
