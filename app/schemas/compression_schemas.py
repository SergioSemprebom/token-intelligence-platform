"""Schemas de entrada e saída dos endpoints de auditoria/compactação de prompts."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.services.prompt_compressor import NIVEIS_VALIDOS


def _validar_texto_nao_vazio(valor: str) -> str:
    if not valor.strip():
        raise ValueError("O texto não pode estar vazio.")
    return valor


class ProblemaEncontradoResponse(BaseModel):
    """Um problema/desperdício identificado pelo auditor de prompts."""

    tipo: str = Field(..., description="Tipo do problema identificado.")
    trecho: str = Field(..., description="Trecho ou expressão de exemplo relacionada ao problema.")
    ocorrencias: int = Field(..., description="Quantidade de ocorrências encontradas.")
    sugestao: str = Field(..., description="Sugestão de correção para o problema.")


class AuditarPromptRequest(BaseModel):
    """Dados de entrada para auditoria de um prompt."""

    texto: str = Field(..., description="Texto/prompt a ser auditado. Não pode ser vazio.")
    modelo: str = Field(
        default="gpt-4o",
        description="Modelo utilizado para determinar o encoding de tokenização.",
        examples=["gpt-4o"],
    )
    termos_protegidos: list[str] = Field(
        default_factory=list,
        description="Termos adicionais que nunca devem ser alterados pelo compactador.",
    )

    @field_validator("texto")
    @classmethod
    def _validar_texto(cls, valor: str) -> str:
        return _validar_texto_nao_vazio(valor)


class AuditarPromptResponse(BaseModel):
    """Diagnóstico de desperdícios de um prompt, sem alterá-lo."""

    modelo: str = Field(..., description="Modelo informado na requisição.")
    encoding: str = Field(..., description="Nome do encoding do tiktoken utilizado.")
    fallback_utilizado: bool = Field(..., description="Indica se houve fallback de encoding.")
    caracteres: int = Field(..., description="Quantidade de caracteres do texto.")
    palavras: int = Field(..., description="Quantidade de palavras do texto.")
    tokens_originais: int = Field(..., description="Quantidade de tokens do texto original.")
    linhas: int = Field(..., description="Quantidade de linhas do texto.")
    frases: int = Field(..., description="Quantidade estimada de frases do texto.")
    quantidade_termos_protegidos: int = Field(
        ..., description="Quantidade de trechos protegidos identificados no texto."
    )
    problemas_encontrados: list[ProblemaEncontradoResponse] = Field(
        ..., description="Lista de problemas/desperdícios identificados."
    )
    nivel_desperdicio: str = Field(..., description="Nível estimado de desperdício: baixo, medio ou alto.")
    recomendacoes: list[str] = Field(..., description="Recomendações textuais para o usuário.")


class CompactarPromptRequest(BaseModel):
    """Dados de entrada para compactação de um prompt."""

    texto: str = Field(..., description="Texto/prompt a ser compactado. Não pode ser vazio.")
    modelo: str = Field(
        default="gpt-4o",
        description="Modelo utilizado para determinar o encoding de tokenização.",
        examples=["gpt-4o"],
    )
    nivel: str = Field(
        default="moderado",
        description="Nível de compactação: conservador, moderado ou agressivo.",
        examples=["moderado"],
    )
    termos_protegidos: list[str] = Field(
        default_factory=list,
        description="Termos adicionais que nunca devem ser alterados pelo compactador.",
    )

    @field_validator("texto")
    @classmethod
    def _validar_texto(cls, valor: str) -> str:
        return _validar_texto_nao_vazio(valor)

    @field_validator("nivel")
    @classmethod
    def _validar_nivel(cls, valor: str) -> str:
        if valor not in NIVEIS_VALIDOS:
            raise ValueError(
                f"Nível de compactação inválido: '{valor}'. Valores aceitos: {sorted(NIVEIS_VALIDOS)}."
            )
        return valor


class AlteracaoAplicadaResponse(BaseModel):
    """Uma alteração concreta aplicada pelo compactador."""

    tipo: str = Field(..., description="Tipo da regra aplicada (ex.: substituicao, remocao).")
    ocorrencias: int = Field(..., description="Quantidade de ocorrências corrigidas por essa regra.")
    nivel: str = Field(..., description="Nível de compactação que originou essa alteração.")
    trecho: str | None = Field(default=None, description="Trecho/expressão afetada, quando aplicável.")
    substituido_por: str | None = Field(
        default=None, description="Texto usado na substituição, quando aplicável."
    )


class CompactarPromptResponse(BaseModel):
    """Resultado da compactação de um prompt, apresentado como sugestão."""

    compactacao_id: uuid.UUID = Field(
        ..., description="Identificador do registro salvo, usado para aprovação posterior."
    )
    texto_original: str = Field(..., description="Texto original informado.")
    texto_compactado: str = Field(..., description="Texto compactado sugerido.")
    nivel: str = Field(..., description="Nível de compactação aplicado.")
    modelo: str = Field(..., description="Modelo utilizado na contagem de tokens.")
    encoding: str = Field(..., description="Nome do encoding do tiktoken utilizado.")
    tokens_originais: int = Field(..., description="Quantidade de tokens do texto original.")
    tokens_compactados: int = Field(..., description="Quantidade de tokens do texto compactado.")
    tokens_economizados: int = Field(..., description="Tokens economizados (pode ser zero).")
    reducao_percentual: float = Field(..., description="Percentual de redução de tokens.")
    caracteres_originais: int = Field(..., description="Caracteres do texto original.")
    caracteres_compactados: int = Field(..., description="Caracteres do texto compactado.")
    alteracoes_aplicadas: list[AlteracaoAplicadaResponse] = Field(
        ..., description="Alterações concretas aplicadas pelo compactador."
    )
    termos_protegidos: list[str] = Field(
        ..., description="Trechos protegidos identificados e preservados no texto."
    )
    avisos: list[str] = Field(..., description="Avisos de risco sobre a compactação.")
    risco: str = Field(..., description="Nível de risco associado ao nível de compactação usado.")
    fallback_utilizado: bool = Field(..., description="Indica se houve fallback de encoding.")
    compactacao_aplicada: bool = Field(
        ..., description="Falso quando não houve benefício e o texto original foi mantido."
    )
    aprovado: bool = Field(default=False, description="Indica se o texto compactado já foi aprovado.")


class ResumoNivelResponse(BaseModel):
    """Resumo de um nível de compactação, para comparação."""

    nivel: str = Field(..., description="Nível comparado (original, conservador, moderado, agressivo).")
    tokens: int = Field(..., description="Quantidade de tokens resultante nesse nível.")
    tokens_economizados: int = Field(..., description="Tokens economizados em relação ao original.")
    reducao_percentual: float = Field(..., description="Percentual de redução de tokens.")
    risco: str = Field(..., description="Nível de risco desse nível de compactação.")
    compactacao_aplicada: bool = Field(..., description="Se houve benefício real de redução de tokens.")
    quantidade_alteracoes: int = Field(..., description="Quantidade de alterações aplicadas nesse nível.")


class CompararCompactacaoRequest(BaseModel):
    """Dados de entrada para comparação entre os níveis de compactação."""

    texto: str = Field(..., description="Texto/prompt a ser comparado. Não pode ser vazio.")
    modelo: str = Field(
        default="gpt-4o",
        description="Modelo utilizado para determinar o encoding de tokenização.",
        examples=["gpt-4o"],
    )
    termos_protegidos: list[str] = Field(
        default_factory=list,
        description="Termos adicionais que nunca devem ser alterados pelo compactador.",
    )

    @field_validator("texto")
    @classmethod
    def _validar_texto(cls, valor: str) -> str:
        return _validar_texto_nao_vazio(valor)


class CompararCompactacaoResponse(BaseModel):
    """Comparação entre o texto original e os três níveis de compactação."""

    modelo: str = Field(..., description="Modelo informado na requisição.")
    encoding: str = Field(..., description="Nome do encoding do tiktoken utilizado.")
    fallback_utilizado: bool = Field(..., description="Indica se houve fallback de encoding.")
    tokens_originais: int = Field(..., description="Quantidade de tokens do texto original.")
    resultados: list[ResumoNivelResponse] = Field(
        ..., description="Resumo de cada nível comparado, incluindo o original."
    )
    melhor_reducao: str = Field(..., description="Nível com a maior redução de tokens, sem considerar risco.")
    recomendado: str = Field(
        ..., description="Nível recomendado, considerando economia de tokens e risco."
    )
    avisos: list[str] = Field(..., description="Avisos gerais sobre a comparação.")


class AprovarCompactacaoRequest(BaseModel):
    """Dados de entrada para aprovar um resultado de compactação já gerado."""

    compactacao_id: uuid.UUID = Field(
        ..., description="Identificador retornado por POST /api/v1/prompts/compactar."
    )


class AprovarCompactacaoResponse(BaseModel):
    """Confirmação da aprovação de um resultado de compactação."""

    compactacao_id: uuid.UUID = Field(..., description="Identificador do registro aprovado.")
    aprovado: bool = Field(..., description="Sempre verdadeiro em uma resposta de sucesso.")
    aprovado_em: datetime = Field(..., description="Momento em que a aprovação foi registrada.")


def alteracoes_para_schema(alteracoes: list[dict[str, Any]]) -> list[AlteracaoAplicadaResponse]:
    """Converte a lista de alterações (dicts) do serviço em schemas de resposta."""
    return [AlteracaoAplicadaResponse(**alteracao) for alteracao in alteracoes]
