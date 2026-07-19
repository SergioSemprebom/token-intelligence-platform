"""Auditor local de prompts: identifica desperdícios sem alterar o texto.

Não aplica nenhuma regra de compactação — apenas mede e relata. A decisão de
compactar (e em qual nível) fica sempre com o usuário, via
`app/services/prompt_compressor.py`.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from app.core.protected_terms import CAMINHO_TERMOS_PADRAO, proteger_termos
from app.core.tokenizer import obter_encoding_info

CAMINHO_REGRAS_PADRAO = Path(__file__).resolve().parent.parent / "config" / "compression_rules.json"

_PADRAO_ESPACOS_DUPLICADOS = re.compile(r"[ \t]{2,}")
_PADRAO_LINHAS_VAZIAS_EXCESSIVAS = re.compile(r"\n{3,}")
_PADRAO_PONTUACAO_REPETIDA = re.compile(r"([!?.,;:])\1+")
_PADRAO_PALAVRAS_DUPLICADAS = re.compile(r"\b(\w+)(?:[ \t]+\1\b)+", re.IGNORECASE)
_PADRAO_FRASES = re.compile(r"[^.!?\n]+[.!?]?")

NIVEL_DESPERDICIO_BAIXO = "baixo"
NIVEL_DESPERDICIO_MEDIO = "medio"
NIVEL_DESPERDICIO_ALTO = "alto"


def _carregar_regras(caminho: Path) -> dict[str, Any]:
    return json.loads(caminho.read_text(encoding="utf-8"))


def _expressoes_redundantes_configuradas(regras: dict[str, Any]) -> list[str]:
    expressoes: list[str] = []
    for nivel in ("moderado", "agressivo"):
        for substituicao in regras.get(nivel, {}).get("substituicoes", []):
            de = substituicao.get("de", "").strip()
            if de:
                expressoes.append(de)
        expressoes.extend(regras.get(nivel, {}).get("remocoes", []))
    return expressoes


def _contar_frases(texto: str) -> int:
    return len([f for f in _PADRAO_FRASES.findall(texto) if f.strip()])


def _detectar_expressoes_redundantes(texto: str, expressoes: list[str]) -> list[dict[str, Any]]:
    problemas: list[dict[str, Any]] = []
    texto_lower = texto.lower()

    for expressao in expressoes:
        ocorrencias = texto_lower.count(expressao.lower())
        if ocorrencias > 0:
            problemas.append(
                {
                    "tipo": "expressao_redundante",
                    "trecho": expressao,
                    "ocorrencias": ocorrencias,
                    "sugestao": "remover ou simplificar (ver nível moderado/agressivo de compactação)",
                }
            )

    return problemas


def _detectar_instrucoes_repetidas(texto: str) -> list[dict[str, Any]]:
    frases = [f.strip().lower() for f in _PADRAO_FRASES.findall(texto) if f.strip()]
    contagem: dict[str, int] = {}

    for frase in frases:
        if len(frase) < 8:
            continue
        contagem[frase] = contagem.get(frase, 0) + 1

    return [
        {
            "tipo": "instrucao_repetida",
            "trecho": frase[:80],
            "ocorrencias": quantidade,
            "sugestao": "consolidar as repetições em uma única instrução",
        }
        for frase, quantidade in contagem.items()
        if quantidade > 1
    ]


def _detectar_problemas_estruturais(texto: str) -> list[dict[str, Any]]:
    problemas: list[dict[str, Any]] = []

    espacos = _PADRAO_ESPACOS_DUPLICADOS.findall(texto)
    if espacos:
        problemas.append(
            {
                "tipo": "espacos_excessivos",
                "trecho": "'  ' (espaços duplicados)",
                "ocorrencias": len(espacos),
                "sugestao": "remover espaços duplicados (nível conservador)",
            }
        )

    linhas_vazias = _PADRAO_LINHAS_VAZIAS_EXCESSIVAS.findall(texto)
    if linhas_vazias:
        problemas.append(
            {
                "tipo": "linhas_vazias_excessivas",
                "trecho": "linhas em branco consecutivas",
                "ocorrencias": len(linhas_vazias),
                "sugestao": "remover linhas vazias excedentes (nível conservador)",
            }
        )

    pontuacao = _PADRAO_PONTUACAO_REPETIDA.findall(texto)
    if pontuacao:
        problemas.append(
            {
                "tipo": "pontuacao_repetida",
                "trecho": "ex.: '!!' ou '??'",
                "ocorrencias": len(pontuacao),
                "sugestao": "reduzir pontuação repetida a um único caractere (nível conservador)",
            }
        )

    palavras_duplicadas = _PADRAO_PALAVRAS_DUPLICADAS.findall(texto)
    if palavras_duplicadas:
        problemas.append(
            {
                "tipo": "palavras_duplicadas",
                "trecho": ", ".join(sorted(set(palavras_duplicadas))[:5]),
                "ocorrencias": len(palavras_duplicadas),
                "sugestao": "remover palavras repetidas em sequência (nível conservador)",
            }
        )

    return problemas


def _calcular_nivel_desperdicio(total_problemas: int) -> str:
    if total_problemas <= 3:
        return NIVEL_DESPERDICIO_BAIXO
    if total_problemas <= 7:
        return NIVEL_DESPERDICIO_MEDIO
    return NIVEL_DESPERDICIO_ALTO


def _gerar_recomendacoes(nivel_desperdicio: str, problemas: list[dict[str, Any]]) -> list[str]:
    recomendacoes: list[str] = []
    tipos_encontrados = {problema["tipo"] for problema in problemas}

    if not problemas:
        recomendacoes.append("Nenhum desperdício relevante encontrado; compactação é opcional.")
        return recomendacoes

    if tipos_encontrados & {
        "espacos_excessivos",
        "linhas_vazias_excessivas",
        "pontuacao_repetida",
        "palavras_duplicadas",
    }:
        recomendacoes.append(
            "Aplique o nível conservador: remove apenas formatação redundante, risco baixo."
        )

    if "expressao_redundante" in tipos_encontrados:
        recomendacoes.append(
            "Aplique o nível moderado: simplifica expressões redundantes, risco médio."
        )

    if "instrucao_repetida" in tipos_encontrados or nivel_desperdicio == NIVEL_DESPERDICIO_ALTO:
        recomendacoes.append(
            "Avalie o nível agressivo apenas com revisão humana antes de substituir o texto original."
        )

    recomendacoes.append(
        "Nunca substitua o texto original automaticamente: revise o texto compactado e aprove antes de usar."
    )

    return recomendacoes


def auditar_prompt(
    texto: str,
    modelo: str = "gpt-4o",
    termos_protegidos: list[str] | None = None,
    caminho_regras: Path = CAMINHO_REGRAS_PADRAO,
    caminho_termos: Path = CAMINHO_TERMOS_PADRAO,
) -> dict[str, Any]:
    """Analisa um prompt e retorna um diagnóstico de desperdícios, sem alterá-lo."""
    texto_normalizado = texto.strip()

    if not texto_normalizado:
        raise ValueError("O texto não pode estar vazio.")

    encoding, fallback_utilizado = obter_encoding_info(modelo)
    tokens = encoding.encode(texto_normalizado)

    regras = _carregar_regras(caminho_regras)
    expressoes_redundantes = _expressoes_redundantes_configuradas(regras)

    _, mapa_protegidos = proteger_termos(
        texto_normalizado, termos_extras=termos_protegidos, caminho_termos=caminho_termos
    )

    problemas: list[dict[str, Any]] = []
    problemas.extend(_detectar_problemas_estruturais(texto_normalizado))
    problemas.extend(_detectar_expressoes_redundantes(texto_normalizado, expressoes_redundantes))
    problemas.extend(_detectar_instrucoes_repetidas(texto_normalizado))

    total_problemas = sum(problema["ocorrencias"] for problema in problemas)
    nivel_desperdicio = _calcular_nivel_desperdicio(total_problemas)

    return {
        "modelo": modelo,
        "encoding": encoding.name,
        "fallback_utilizado": fallback_utilizado,
        "caracteres": len(texto_normalizado),
        "palavras": len(texto_normalizado.split()),
        "tokens_originais": len(tokens),
        "linhas": len(texto_normalizado.splitlines()),
        "frases": _contar_frases(texto_normalizado),
        "quantidade_termos_protegidos": len(mapa_protegidos),
        "problemas_encontrados": problemas,
        "nivel_desperdicio": nivel_desperdicio,
        "recomendacoes": _gerar_recomendacoes(nivel_desperdicio, problemas),
    }
