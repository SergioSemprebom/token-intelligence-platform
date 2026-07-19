"""Schemas de entrada e saída do endpoint de comparação entre modelos."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class CompararModelosRequest(BaseModel):
    """Dados de entrada para comparação de tokenização entre modelos."""

    texto: str = Field(
        ...,
        description="Texto a ser comparado entre os modelos. Não pode ser vazio.",
        examples=["Texto para comparar"],
    )
    modelos: list[str] = Field(
        ...,
        min_length=1,
        description="Lista de modelos a comparar. Deve conter ao menos um modelo.",
        examples=[["gpt-4o", "o3", "gpt-4"]],
    )

    @field_validator("texto")
    @classmethod
    def validar_texto_nao_vazio(cls, valor: str) -> str:
        """Garante que o texto informado não seja vazio ou composto só de espaços."""
        if not valor.strip():
            raise ValueError("O texto não pode estar vazio.")
        return valor


class ResultadoComparacaoResponse(BaseModel):
    """Resultado da comparação de tokenização para um modelo específico."""

    modelo_solicitado: str = Field(..., description="Modelo solicitado na requisição.")
    encoding_utilizado: str = Field(
        ..., description="Nome do encoding do tiktoken efetivamente utilizado."
    )
    tokens: int = Field(..., description="Quantidade de tokens do texto para o modelo.")
    caracteres: int = Field(..., description="Quantidade de caracteres do texto.")
    palavras: int = Field(..., description="Quantidade de palavras do texto.")
    bytes_utf8: int = Field(..., description="Tamanho do texto em bytes UTF-8.")
    media_caracteres_por_token: float = Field(
        ..., description="Média de caracteres por token."
    )
    fallback_utilizado: bool = Field(
        ...,
        description="Indica se o modelo não foi reconhecido e houve fallback para o200k_base.",
    )
    aviso: str | None = Field(
        default=None,
        description="Mensagem explicando o fallback, quando aplicável.",
    )


class CompararModelosResponse(BaseModel):
    """Resultado da comparação de tokenização entre os modelos solicitados."""

    resultados: list[ResultadoComparacaoResponse] = Field(
        ..., description="Resultados da comparação, um por modelo solicitado."
    )
