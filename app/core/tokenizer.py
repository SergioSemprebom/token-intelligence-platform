from time import perf_counter
from typing import Any

import tiktoken


ENCODING_PADRAO = "o200k_base"


def obter_encoding_info(modelo: str) -> tuple[tiktoken.Encoding, bool]:
    """
    Retorna a codificação do modelo e indica se houve fallback.

    Caso o modelo não seja reconhecido pelo TikToken, utiliza a
    codificação o200k_base e sinaliza o fallback no segundo valor
    retornado, para que o chamador não precise ocultar essa informação.
    """
    try:
        return tiktoken.encoding_for_model(modelo), False
    except KeyError:
        return tiktoken.get_encoding(ENCODING_PADRAO), True


def obter_encoding(modelo: str) -> tiktoken.Encoding:
    """
    Retorna a codificação correspondente ao modelo informado.

    Caso o modelo não seja reconhecido pelo TikToken,
    utiliza a codificação o200k_base.
    """
    encoding, _ = obter_encoding_info(modelo)
    return encoding


def analisar_texto(
    texto: str,
    modelo: str = "gpt-4o",
    incluir_token_ids: bool = False,
) -> dict[str, Any]:
    """
    Analisa um texto e retorna métricas de tokenização.
    """
    texto_normalizado = texto.strip()

    if not texto_normalizado:
        raise ValueError("O texto não pode estar vazio.")

    inicio = perf_counter()

    encoding = obter_encoding(modelo)
    token_ids = encoding.encode(texto_normalizado)

    tempo_processamento_ms = (perf_counter() - inicio) * 1000

    quantidade_tokens = len(token_ids)

    resultado: dict[str, Any] = {
        "modelo": modelo,
        "encoding": encoding.name,
        "caracteres": len(texto_normalizado),
        "palavras": len(texto_normalizado.split()),
        "tokens": quantidade_tokens,
        "bytes_utf8": len(texto_normalizado.encode("utf-8")),
        "media_caracteres_por_token": round(
            len(texto_normalizado) / quantidade_tokens,
            2,
        ),
        "tempo_processamento_ms": round(
            tempo_processamento_ms,
            4,
        ),
    }

    if incluir_token_ids:
        resultado["token_ids"] = token_ids

    return resultado