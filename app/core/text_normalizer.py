"""Regras conservadoras de normalização textual (nível 'conservador').

Todas as funções operam sobre texto já protegido por
`app/core/protected_terms.py` (números, datas, identificadores etc. já viram
marcadores opacos antes de chegar aqui), então nenhuma delas precisa se
preocupar em preservar esse tipo de conteúdo — a proteção acontece em uma
camada anterior. Cada função devolve o texto resultante e a quantidade de
ocorrências corrigidas, para alimentar `alteracoes_aplicadas` no compressor.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass

_PADRAO_ESPACOS_DUPLICADOS = re.compile(r"[ \t]{2,}")
_PADRAO_LINHAS_VAZIAS_EXCESSIVAS = re.compile(r"\n{3,}")
_PADRAO_PONTUACAO_REPETIDA = re.compile(r"([!?.,;:])\1+")
_PADRAO_PALAVRAS_DUPLICADAS = re.compile(r"\b(\w+)(?:[ \t]+\1\b)+", re.IGNORECASE)
_PADRAO_ESPACO_ANTES_PONTUACAO = re.compile(r"[ \t]+([!?.,;:])")
_PADRAO_ESPACO_APOS_ABRE_PARENTESES = re.compile(r"\([ \t]+")
_PADRAO_ESPACO_ANTES_FECHA_PARENTESES = re.compile(r"[ \t]+\)")


@dataclass(frozen=True)
class AlteracaoAplicada:
    """Descreve uma regra de compactação que alterou o texto."""

    tipo: str
    ocorrencias: int
    nivel: str


def remover_espacos_duplicados(texto: str) -> tuple[str, int]:
    """Reduz sequências de espaços/tabs consecutivos a um único espaço."""
    resultado, quantidade = _PADRAO_ESPACOS_DUPLICADOS.subn(" ", texto)
    return resultado, quantidade


def remover_linhas_vazias_excessivas(texto: str) -> tuple[str, int]:
    """Reduz três ou mais quebras de linha seguidas a uma linha vazia."""
    resultado, quantidade = _PADRAO_LINHAS_VAZIAS_EXCESSIVAS.subn("\n\n", texto)
    return resultado, quantidade


def remover_pontuacao_repetida(texto: str) -> tuple[str, int]:
    """Reduz pontuação repetida (ex.: '!!!', '??') a um único caractere."""
    resultado, quantidade = _PADRAO_PONTUACAO_REPETIDA.subn(r"\1", texto)
    return resultado, quantidade


def remover_palavras_consecutivas_duplicadas(texto: str) -> tuple[str, int]:
    """Remove repetições literais de uma mesma palavra em sequência."""
    resultado, quantidade = _PADRAO_PALAVRAS_DUPLICADAS.subn(r"\1", texto)
    return resultado, quantidade


def remover_espaco_antes_pontuacao(texto: str) -> tuple[str, int]:
    """Remove espaços antes de pontuação (ex.: 'texto ,' -> 'texto,')."""
    resultado, quantidade = _PADRAO_ESPACO_ANTES_PONTUACAO.subn(r"\1", texto)
    return resultado, quantidade


def remover_espaco_apos_abre_parenteses(texto: str) -> tuple[str, int]:
    """Remove espaços logo após um parêntese de abertura."""
    resultado, quantidade = _PADRAO_ESPACO_APOS_ABRE_PARENTESES.subn("(", texto)
    return resultado, quantidade


def remover_espaco_antes_fecha_parenteses(texto: str) -> tuple[str, int]:
    """Remove espaços logo antes de um parêntese de fechamento."""
    resultado, quantidade = _PADRAO_ESPACO_ANTES_FECHA_PARENTESES.subn(")", texto)
    return resultado, quantidade


def remover_linhas_repetidas_consecutivas(texto: str) -> tuple[str, int]:
    """Remove linhas idênticas (ignorando espaços) repetidas em sequência."""
    linhas = texto.split("\n")
    resultado: list[str] = []
    quantidade = 0

    for linha in linhas:
        anterior_normalizada = resultado[-1].strip().lower() if resultado else None
        if linha.strip() and linha.strip().lower() == anterior_normalizada:
            quantidade += 1
            continue
        resultado.append(linha)

    return "\n".join(resultado), quantidade


def remover_saudacoes_isoladas(texto: str, saudacoes: list[str]) -> tuple[str, int]:
    """Remove linhas compostas somente por uma saudação simples e isolada."""
    if not saudacoes:
        return texto, 0

    saudacoes_normalizadas = {s.strip().lower() for s in saudacoes}
    linhas = texto.split("\n")
    resultado: list[str] = []
    quantidade = 0

    for linha in linhas:
        linha_normalizada = linha.strip().lower().rstrip("!.,")
        if linha_normalizada in saudacoes_normalizadas:
            quantidade += 1
            continue
        resultado.append(linha)

    return "\n".join(resultado), quantidade


def normalizar_conservador(
    texto: str,
    saudacoes_isoladas: list[str] | None = None,
) -> tuple[str, list[AlteracaoAplicada]]:
    """Aplica todas as regras conservadoras em sequência sobre o texto.

    Retorna o texto resultante e a lista de alterações que de fato tiveram
    efeito (regras sem nenhuma ocorrência não aparecem na lista).
    """
    alteracoes: list[AlteracaoAplicada] = []
    resultado = texto

    etapas: list[tuple[str, Callable[[str], tuple[str, int]]]] = [
        ("palavras_consecutivas_duplicadas", remover_palavras_consecutivas_duplicadas),
        ("pontuacao_repetida", remover_pontuacao_repetida),
        ("espaco_antes_pontuacao", remover_espaco_antes_pontuacao),
        ("espaco_apos_abre_parenteses", remover_espaco_apos_abre_parenteses),
        ("espaco_antes_fecha_parenteses", remover_espaco_antes_fecha_parenteses),
        ("espacos_duplicados", remover_espacos_duplicados),
        ("linhas_repetidas_consecutivas", remover_linhas_repetidas_consecutivas),
        ("linhas_vazias_excessivas", remover_linhas_vazias_excessivas),
    ]

    for tipo, funcao in etapas:
        resultado, quantidade = funcao(resultado)
        if quantidade > 0:
            alteracoes.append(AlteracaoAplicada(tipo=tipo, ocorrencias=quantidade, nivel="conservador"))

    resultado, quantidade_saudacoes = remover_saudacoes_isoladas(
        resultado, saudacoes_isoladas or []
    )
    if quantidade_saudacoes > 0:
        alteracoes.append(
            AlteracaoAplicada(tipo="saudacao_isolada", ocorrencias=quantidade_saudacoes, nivel="conservador")
        )

    return resultado.strip(), alteracoes
