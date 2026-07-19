"""Divisão de textos grandes em blocos por quantidade de tokens."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.tokenizer import obter_encoding


@dataclass(frozen=True)
class BlocoTexto:
    """Representa um bloco de texto resultante da divisão por tokens."""

    indice: int
    texto: str
    quantidade_tokens: int
    token_inicial: int
    token_final: int


def dividir_texto_por_tokens(
    texto: str,
    modelo: str = "gpt-4o",
    limite_tokens: int = 500,
    sobreposicao: int = 0,
) -> list[BlocoTexto]:
    """
    Divide um texto em blocos que respeitam um limite máximo de tokens.

    A divisão é feita com base na contagem real de tokens do modelo
    informado, nunca por quantidade de caracteres. Quando informada,
    a sobreposição repete os últimos tokens do bloco anterior no
    início do bloco seguinte, para preservar contexto entre blocos.
    """
    if limite_tokens <= 0:
        raise ValueError("O limite de tokens deve ser maior que zero.")

    if sobreposicao < 0:
        raise ValueError("A sobreposição não pode ser negativa.")

    if sobreposicao >= limite_tokens:
        raise ValueError("A sobreposição deve ser menor que o limite de tokens.")

    texto_normalizado = texto.strip()

    if not texto_normalizado:
        raise ValueError("O texto não pode estar vazio.")

    encoding = obter_encoding(modelo)
    tokens = encoding.encode(texto_normalizado)
    total_tokens = len(tokens)

    passo = limite_tokens - sobreposicao
    blocos: list[BlocoTexto] = []
    inicio = 0
    indice = 0

    while inicio < total_tokens:
        fim = min(inicio + limite_tokens, total_tokens)
        tokens_bloco = tokens[inicio:fim]

        blocos.append(
            BlocoTexto(
                indice=indice,
                texto=encoding.decode(tokens_bloco),
                quantidade_tokens=len(tokens_bloco),
                token_inicial=inicio,
                token_final=fim - 1,
            )
        )

        if fim == total_tokens:
            break

        indice += 1
        inicio += passo

    return blocos
