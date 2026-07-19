"""Schemas de entrada e saída do endpoint de análise de texto."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class AnalisarTextoRequest(BaseModel):
    """Dados de entrada para análise de tokenização de um texto."""

    texto: str = Field(
        ...,
        description="Texto a ser analisado. Não pode ser vazio.",
        examples=["Texto para analisar"],
    )
    modelo: str = Field(
        default="gpt-4o",
        description="Modelo utilizado para determinar o encoding de tokenização.",
        examples=["gpt-4o"],
    )
    incluir_token_ids: bool = Field(
        default=False,
        description="Quando verdadeiro, inclui a lista de token_ids na resposta.",
        examples=[False],
    )

    @field_validator("texto")
    @classmethod
    def validar_texto_nao_vazio(cls, valor: str) -> str:
        """Garante que o texto informado não seja vazio ou composto só de espaços."""
        if not valor.strip():
            raise ValueError("O texto não pode estar vazio.")
        return valor


class AnalisarTextoResponse(BaseModel):
    """Resultado da análise de tokenização de um texto."""

    modelo: str = Field(..., description="Modelo informado na requisição.")
    encoding: str = Field(..., description="Nome do encoding do tiktoken utilizado.")
    caracteres: int = Field(..., description="Quantidade de caracteres do texto.")
    palavras: int = Field(..., description="Quantidade de palavras do texto.")
    tokens: int = Field(..., description="Quantidade de tokens do texto.")
    bytes_utf8: int = Field(..., description="Tamanho do texto em bytes UTF-8.")
    media_caracteres_por_token: float = Field(
        ..., description="Média de caracteres por token."
    )
    tempo_processamento_ms: float = Field(
        ..., description="Tempo de processamento da tokenização, em milissegundos."
    )
    fallback_utilizado: bool = Field(
        ...,
        description=(
            "Indica se o modelo informado não foi reconhecido pelo tiktoken e houve "
            "fallback para o encoding o200k_base."
        ),
    )
    token_ids: list[int] | None = Field(
        default=None,
        description="Lista de token_ids do texto, presente somente quando solicitada.",
    )
