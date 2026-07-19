"""Schemas de entrada e saída do endpoint de estimativa de custo."""

from __future__ import annotations

from pydantic import BaseModel, Field


class EstimarCustoRequest(BaseModel):
    """Dados de entrada para estimativa de custo de uso de tokens."""

    modelo: str = Field(
        ...,
        min_length=1,
        description="Nome do modelo configurado em app/config/model_prices.json.",
        examples=["gpt-4o"],
    )
    tokens_entrada: int = Field(
        ...,
        ge=0,
        description="Quantidade de tokens de entrada. Não pode ser negativa.",
        examples=[115],
    )
    tokens_saida: int = Field(
        ...,
        ge=0,
        description="Quantidade de tokens de saída. Não pode ser negativa.",
        examples=[100],
    )


class EstimarCustoResponse(BaseModel):
    """Resultado da estimativa de custo de uso de tokens."""

    modelo: str = Field(..., description="Modelo utilizado na estimativa.")
    tokens_entrada: int = Field(..., description="Quantidade de tokens de entrada.")
    tokens_saida: int = Field(..., description="Quantidade de tokens de saída.")
    total_tokens: int = Field(..., description="Soma de tokens de entrada e saída.")
    custo_entrada: str = Field(
        ..., description="Custo estimado dos tokens de entrada, como string decimal."
    )
    custo_saida: str = Field(
        ..., description="Custo estimado dos tokens de saída, como string decimal."
    )
    custo_total: str = Field(
        ..., description="Custo total estimado, como string decimal."
    )
    moeda: str = Field(default="USD", description="Moeda dos valores retornados.")
    aviso: str = Field(
        ..., description="Aviso sobre a natureza demonstrativa dos preços utilizados."
    )
