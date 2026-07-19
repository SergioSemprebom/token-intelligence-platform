"""Comparação de tokenização de um mesmo texto entre diferentes modelos."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.tokenizer import obter_encoding_info


@dataclass(frozen=True)
class ResultadoComparacaoModelo:
    """Resultado da comparação de tokenização para um modelo específico."""

    modelo_solicitado: str
    encoding_utilizado: str
    tokens: int
    caracteres: int
    palavras: int
    bytes_utf8: int
    media_caracteres_por_token: float
    fallback_utilizado: bool


def comparar_modelos(texto: str, modelos: list[str]) -> list[ResultadoComparacaoModelo]:
    """
    Compara a tokenização de um mesmo texto entre diferentes modelos.

    Quando um modelo não é reconhecido pelo tiktoken, o resultado
    correspondente indica explicitamente que houve fallback para a
    codificação o200k_base, sem ocultar essa informação do usuário.
    """
    texto_normalizado = texto.strip()

    if not texto_normalizado:
        raise ValueError("O texto não pode estar vazio.")

    return [_comparar_modelo(texto_normalizado, modelo) for modelo in modelos]


def _comparar_modelo(texto: str, modelo: str) -> ResultadoComparacaoModelo:
    modelo_normalizado = modelo.strip().lower()
    encoding, fallback_utilizado = obter_encoding_info(modelo_normalizado)
    tokens = encoding.encode(texto)
    quantidade_tokens = len(tokens)

    return ResultadoComparacaoModelo(
        modelo_solicitado=modelo_normalizado,
        encoding_utilizado=encoding.name,
        tokens=quantidade_tokens,
        caracteres=len(texto),
        palavras=len(texto.split()),
        bytes_utf8=len(texto.encode("utf-8")),
        media_caracteres_por_token=round(len(texto) / quantidade_tokens, 2),
        fallback_utilizado=fallback_utilizado,
    )
