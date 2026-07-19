"""Proteção de termos essenciais contra alteração pelo compactador de prompts.

Antes de qualquer regra de compactação ser aplicada, os trechos protegidos
(números, datas, valores monetários, identificadores técnicos, URLs, blocos de
código etc.) são substituídos por marcadores opacos (delimitados por `\\x00`,
um caractere de controle que nunca aparece em texto normal e que nenhuma regra
de compactação reconhece). Depois de todas as regras serem aplicadas, os
marcadores são substituídos de volta pelo conteúdo original, garantindo que
esses trechos nunca sejam removidos, reordenados ou alterados.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

CAMINHO_TERMOS_PADRAO = Path(__file__).resolve().parent.parent / "config" / "protected_terms.json"

_INICIO_MARCADOR = "\x00PROT"
_FIM_MARCADOR = "FIM\x00"

# Padrões aplicados em ordem: cada padrão só enxerga o texto já restante dos
# anteriores (os trechos já protegidos viram marcadores opacos), então a
# ordem vai do mais específico/abrangente para o mais genérico, evitando que
# um número dentro de uma data ou de uma URL seja protegido duas vezes.
_PADROES_PROTEGIDOS: list[tuple[str, re.Pattern[str]]] = [
    ("bloco_codigo", re.compile(r"```.*?```", re.DOTALL)),
    ("bloco_codigo_inline", re.compile(r"`[^`\n]+`")),
    ("url", re.compile(r"\bhttps?://\S+\b|\bwww\.\S+\b")),
    ("caminho_arquivo", re.compile(r"[A-Za-z]:\\[^\s\"']+|\.{1,2}/[^\s\"']+|/[^\s\"']+/[^\s\"']+")),
    ("host_porta", re.compile(r"\b[\w.-]+:\d{2,5}\b")),
    ("nome_entre_aspas", re.compile(r"\"[^\"\n]+\"|'[^'\n]+'")),
    ("valor_monetario", re.compile(r"R\$\s?\d{1,3}(?:\.\d{3})*(?:,\d{1,2})?")),
    ("percentual", re.compile(r"\b\d+(?:[.,]\d+)?\s?%")),
    ("data", re.compile(r"\b\d{4}-\d{2}-\d{2}\b|\b\d{2}/\d{2}/\d{4}\b")),
    ("identificador_pontuado", re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*\b")),
    ("identificador_com_underscore", re.compile(r"\b[A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)+\b")),
    ("identificador_camel_case", re.compile(r"\b[a-z][a-z0-9]*(?:[A-Z][a-z0-9]*)+\b")),
    ("palavra_maiuscula", re.compile(r"\b[A-Z]{2,}\b")),
    ("numero", re.compile(r"\b\d+(?:[.,]\d+)*\b")),
]


def carregar_termos_tecnicos(caminho: Path = CAMINHO_TERMOS_PADRAO) -> list[str]:
    """Carrega os termos técnicos configurados em app/config/protected_terms.json."""
    conteudo = json.loads(caminho.read_text(encoding="utf-8"))
    return list(conteudo.get("termos", []))


def _proteger_padrao(
    texto: str,
    padrao: re.Pattern[str],
    mapa: dict[str, str],
) -> str:
    def _substituir(match: re.Match[str]) -> str:
        marcador = f"{_INICIO_MARCADOR}{len(mapa)}{_FIM_MARCADOR}"
        mapa[marcador] = match.group(0)
        return marcador

    return padrao.sub(_substituir, texto)


def proteger_termos(
    texto: str,
    termos_extras: list[str] | None = None,
    caminho_termos: Path = CAMINHO_TERMOS_PADRAO,
) -> tuple[str, dict[str, str]]:
    """Substitui trechos protegidos por marcadores opacos.

    Retorna o texto com marcadores no lugar dos trechos protegidos e um mapa
    de marcador -> conteúdo original, usado por `restaurar_termos` para
    devolver o texto ao seu estado final.
    """
    mapa: dict[str, str] = {}
    texto_protegido = texto

    for _, padrao in _PADROES_PROTEGIDOS:
        texto_protegido = _proteger_padrao(texto_protegido, padrao, mapa)

    termos_tecnicos = carregar_termos_tecnicos(caminho_termos) + list(termos_extras or [])
    termos_unicos = sorted(set(termos_tecnicos), key=len, reverse=True)

    if termos_unicos:
        padrao_termos = re.compile(
            "|".join(re.escape(termo) for termo in termos_unicos),
            re.IGNORECASE,
        )
        texto_protegido = _proteger_padrao(texto_protegido, padrao_termos, mapa)

    return texto_protegido, mapa


def restaurar_termos(texto_protegido: str, mapa: dict[str, str]) -> str:
    """Substitui os marcadores opacos pelo conteúdo original protegido."""
    texto_restaurado = texto_protegido
    for marcador, original in mapa.items():
        texto_restaurado = texto_restaurado.replace(marcador, original)
    return texto_restaurado


def listar_termos_protegidos_encontrados(mapa: dict[str, str]) -> list[str]:
    """Retorna, sem duplicatas, os trechos que foram protegidos em um texto."""
    return sorted(set(mapa.values()))
