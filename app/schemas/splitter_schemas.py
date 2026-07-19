"""Schemas de entrada e saída do endpoint de divisão de texto por tokens."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class DividirTextoRequest(BaseModel):
    """Dados de entrada para divisão de um texto em blocos de tokens."""

    texto: str = Field(
        ...,
        description="Texto a ser dividido em blocos. Não pode ser vazio.",
        examples=["Texto longo"],
    )
    modelo: str = Field(
        default="gpt-4o",
        description="Modelo utilizado para determinar o encoding de tokenização.",
        examples=["gpt-4o"],
    )
    limite_tokens: int = Field(
        ...,
        gt=0,
        description="Quantidade máxima de tokens por bloco. Deve ser maior que zero.",
        examples=[100],
    )
    sobreposicao_tokens: int = Field(
        default=0,
        ge=0,
        description=(
            "Quantidade de tokens repetidos entre blocos consecutivos. Deve ser menor "
            "que o limite de tokens."
        ),
        examples=[10],
    )

    @field_validator("texto")
    @classmethod
    def validar_texto_nao_vazio(cls, valor: str) -> str:
        """Garante que o texto informado não seja vazio ou composto só de espaços."""
        if not valor.strip():
            raise ValueError("O texto não pode estar vazio.")
        return valor


class BlocoTextoResponse(BaseModel):
    """Um bloco de texto resultante da divisão por tokens."""

    indice: int = Field(..., description="Posição do bloco na sequência de blocos.")
    texto: str = Field(..., description="Conteúdo textual do bloco.")
    quantidade_tokens: int = Field(..., description="Quantidade de tokens do bloco.")
    token_inicial: int = Field(
        ..., description="Índice do primeiro token do bloco no texto original."
    )
    token_final: int = Field(
        ..., description="Índice do último token do bloco no texto original."
    )


class DividirTextoResponse(BaseModel):
    """Resultado da divisão de um texto em blocos de tokens."""

    modelo: str = Field(..., description="Modelo informado na requisição.")
    total_blocos: int = Field(..., description="Quantidade total de blocos gerados.")
    total_tokens_original: int = Field(
        ..., description="Quantidade total de tokens do texto original."
    )
    blocos: list[BlocoTextoResponse] = Field(
        ..., description="Lista de blocos gerados a partir do texto original."
    )
