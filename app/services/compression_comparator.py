"""Comparação entre os níveis de compactação de prompts (local, sem IA)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.protected_terms import CAMINHO_TERMOS_PADRAO
from app.core.tokenizer import obter_encoding_info
from app.services.prompt_compressor import (
    CAMINHO_REGRAS_PADRAO,
    NIVEL_AGRESSIVO,
    NIVEL_CONSERVADOR,
    NIVEL_MODERADO,
    ResultadoCompactacaoPrompt,
    compactar_prompt,
)

_ORDEM_NIVEIS = (NIVEL_CONSERVADOR, NIVEL_MODERADO, NIVEL_AGRESSIVO)

_AVISO_AGRESSIVO_MELHOR_REDUCAO = (
    "O nível agressivo teve a maior redução de tokens, mas isso não significa que ele "
    "deva ser aplicado automaticamente: revise o texto compactado com atenção antes de aprovar."
)


def _resumir_resultado(resultado: ResultadoCompactacaoPrompt) -> dict[str, Any]:
    return {
        "nivel": resultado.nivel,
        "tokens": resultado.tokens_compactados,
        "tokens_economizados": resultado.tokens_economizados,
        "reducao_percentual": resultado.reducao_percentual,
        "risco": resultado.risco,
        "compactacao_aplicada": resultado.compactacao_aplicada,
        "quantidade_alteracoes": len(resultado.alteracoes_aplicadas),
    }


def _escolher_melhor_reducao(resultados: dict[str, ResultadoCompactacaoPrompt]) -> str:
    melhor_nivel = "nenhum"
    melhor_economia = 0

    for nivel in _ORDEM_NIVEIS:
        economia = resultados[nivel].tokens_economizados
        if economia > melhor_economia:
            melhor_economia = economia
            melhor_nivel = nivel

    return melhor_nivel


def _recomendar_nivel(resultados: dict[str, ResultadoCompactacaoPrompt]) -> str:
    """Recomenda o nível considerando economia e risco, não apenas a maior redução.

    O nível moderado é preferido por equilibrar economia de tokens e risco
    médio; o agressivo só é recomendado quando nenhum outro nível traz
    benefício, e mesmo assim exige revisão humana explícita.
    """
    if resultados[NIVEL_MODERADO].compactacao_aplicada:
        return NIVEL_MODERADO
    if resultados[NIVEL_CONSERVADOR].compactacao_aplicada:
        return NIVEL_CONSERVADOR
    if resultados[NIVEL_AGRESSIVO].compactacao_aplicada:
        return NIVEL_AGRESSIVO
    return "nenhum"


def comparar_niveis(
    texto: str,
    modelo: str = "gpt-4o",
    termos_protegidos: list[str] | None = None,
    caminho_regras: Path = CAMINHO_REGRAS_PADRAO,
    caminho_termos: Path = CAMINHO_TERMOS_PADRAO,
) -> dict[str, Any]:
    """Compacta o mesmo texto nos três níveis e compara os resultados.

    Nunca seleciona automaticamente o nível agressivo como "recomendado"
    apenas por ele reduzir mais tokens — isso fica explícito em
    `melhor_reducao` (que pode ser o agressivo) versus `recomendado` (que
    pondera risco).
    """
    texto_normalizado = texto.strip()
    if not texto_normalizado:
        raise ValueError("O texto não pode estar vazio.")

    encoding, fallback_utilizado = obter_encoding_info(modelo)
    tokens_originais = len(encoding.encode(texto_normalizado))

    resultados_por_nivel = {
        nivel: compactar_prompt(
            texto=texto_normalizado,
            nivel=nivel,
            modelo=modelo,
            termos_protegidos=termos_protegidos,
            caminho_regras=caminho_regras,
            caminho_termos=caminho_termos,
        )
        for nivel in _ORDEM_NIVEIS
    }

    melhor_reducao = _escolher_melhor_reducao(resultados_por_nivel)
    recomendado = _recomendar_nivel(resultados_por_nivel)

    avisos = []
    if melhor_reducao == NIVEL_AGRESSIVO:
        avisos.append(_AVISO_AGRESSIVO_MELHOR_REDUCAO)

    return {
        "modelo": modelo,
        "encoding": encoding.name,
        "fallback_utilizado": fallback_utilizado,
        "tokens_originais": tokens_originais,
        "resultados": [
            {"nivel": "original", "tokens": tokens_originais, "tokens_economizados": 0,
             "reducao_percentual": 0.0, "risco": "nenhum", "compactacao_aplicada": False,
             "quantidade_alteracoes": 0},
            *[_resumir_resultado(resultados_por_nivel[nivel]) for nivel in _ORDEM_NIVEIS],
        ],
        "melhor_reducao": melhor_reducao,
        "recomendado": recomendado,
        "avisos": avisos,
        "detalhes": resultados_por_nivel,
    }
