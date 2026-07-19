"""Compactador local de prompts, por regras (conservador/moderado/agressivo).

Princípio fundamental: nenhuma regra promete preservação perfeita de
significado. O resultado é sempre apresentado como sugestão — a aprovação de
uso é um passo humano separado (ver `app/services/processing_history.py` e o
endpoint `POST /api/v1/prompts/aprovar`), nunca automática.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.core.protected_terms import (
    CAMINHO_TERMOS_PADRAO,
    listar_termos_protegidos_encontrados,
    proteger_termos,
    restaurar_termos,
)
from app.core.text_normalizer import normalizar_conservador
from app.core.tokenizer import obter_encoding_info

CAMINHO_REGRAS_PADRAO = Path(__file__).resolve().parent.parent / "config" / "compression_rules.json"

NIVEL_CONSERVADOR = "conservador"
NIVEL_MODERADO = "moderado"
NIVEL_AGRESSIVO = "agressivo"

NIVEIS_VALIDOS = {NIVEL_CONSERVADOR, NIVEL_MODERADO, NIVEL_AGRESSIVO}

RISCO_POR_NIVEL = {
    NIVEL_CONSERVADOR: "baixo",
    NIVEL_MODERADO: "medio",
    NIVEL_AGRESSIVO: "alto",
}

_AVISO_APROVACAO_HUMANA = (
    "Aprovação humana é obrigatória antes de substituir o texto original "
    "(ver POST /api/v1/prompts/aprovar). O texto compactado é sempre uma sugestão."
)

_AVISOS_POR_NIVEL = {
    NIVEL_CONSERVADOR: (
        "Risco baixo: apenas espaçamento, pontuação e duplicidades evidentes foram ajustados."
    ),
    NIVEL_MODERADO: (
        "Risco médio: expressões consideradas redundantes foram simplificadas ou removidas; "
        "revise o resultado antes de usar."
    ),
    NIVEL_AGRESSIVO: (
        "Risco alto: frases foram reescritas ou removidas de forma mais agressiva. "
        "Não há garantia de preservação perfeita do significado — revise cuidadosamente "
        "e nunca aplique automaticamente."
    ),
}


@dataclass(frozen=True)
class ResultadoCompactacaoPrompt:
    """Resultado completo de uma compactação de prompt."""

    texto_original: str
    texto_compactado: str
    nivel: str
    modelo: str
    encoding: str
    tokens_originais: int
    tokens_compactados: int
    tokens_economizados: int
    reducao_percentual: float
    caracteres_originais: int
    caracteres_compactados: int
    alteracoes_aplicadas: list[dict[str, Any]] = field(default_factory=list)
    termos_protegidos: list[str] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)
    risco: str = "baixo"
    fallback_utilizado: bool = False
    compactacao_aplicada: bool = True


def _carregar_regras(caminho: Path) -> dict[str, Any]:
    return json.loads(caminho.read_text(encoding="utf-8"))


def _aplicar_substituicoes(
    texto: str, substituicoes: list[dict[str, str]], nivel: str
) -> tuple[str, list[dict[str, Any]]]:
    resultado = texto
    alteracoes: list[dict[str, Any]] = []

    for substituicao in substituicoes:
        de = substituicao.get("de", "")
        para = substituicao.get("para", "")
        if not de:
            continue

        padrao = re.compile(re.escape(de), re.IGNORECASE)
        resultado, quantidade = padrao.subn(para, resultado)

        if quantidade > 0:
            alteracoes.append(
                {
                    "tipo": "substituicao",
                    "trecho": de,
                    "substituido_por": para or "(removido)",
                    "ocorrencias": quantidade,
                    "nivel": nivel,
                }
            )

    return resultado, alteracoes


def _aplicar_remocoes(
    texto: str, remocoes: list[str], nivel: str
) -> tuple[str, list[dict[str, Any]]]:
    resultado = texto
    alteracoes: list[dict[str, Any]] = []

    for frase in remocoes:
        if not frase:
            continue

        padrao = re.compile(re.escape(frase), re.IGNORECASE)
        resultado, quantidade = padrao.subn("", resultado)

        if quantidade > 0:
            alteracoes.append(
                {
                    "tipo": "remocao",
                    "trecho": frase,
                    "ocorrencias": quantidade,
                    "nivel": nivel,
                }
            )

    return resultado, alteracoes


def compactar_prompt(
    texto: str,
    nivel: str,
    modelo: str = "gpt-4o",
    termos_protegidos: list[str] | None = None,
    caminho_regras: Path = CAMINHO_REGRAS_PADRAO,
    caminho_termos: Path = CAMINHO_TERMOS_PADRAO,
) -> ResultadoCompactacaoPrompt:
    """Compacta um prompt aplicando as regras locais do nível informado.

    O nível 'moderado' inclui as regras do 'conservador'; o 'agressivo' inclui
    as de ambos. Se o texto resultante não reduzir a quantidade de tokens em
    relação ao original, o texto original é preservado e
    `compactacao_aplicada` retorna `False`.
    """
    if nivel not in NIVEIS_VALIDOS:
        raise ValueError(
            f"Nível de compactação inválido: '{nivel}'. Valores aceitos: {sorted(NIVEIS_VALIDOS)}."
        )

    texto_normalizado = texto.strip()
    if not texto_normalizado:
        raise ValueError("O texto não pode estar vazio.")

    regras = _carregar_regras(caminho_regras)

    texto_protegido, mapa_protegidos = proteger_termos(
        texto_normalizado, termos_extras=termos_protegidos, caminho_termos=caminho_termos
    )

    alteracoes_aplicadas: list[dict[str, Any]] = []

    saudacoes_isoladas = regras.get(NIVEL_CONSERVADOR, {}).get("saudacoes_isoladas", [])
    resultado, alteracoes_conservador = normalizar_conservador(texto_protegido, saudacoes_isoladas)
    alteracoes_aplicadas.extend(
        {"tipo": a.tipo, "ocorrencias": a.ocorrencias, "nivel": a.nivel} for a in alteracoes_conservador
    )

    if nivel in (NIVEL_MODERADO, NIVEL_AGRESSIVO):
        resultado, alteracoes_moderado = _aplicar_substituicoes(
            resultado, regras.get(NIVEL_MODERADO, {}).get("substituicoes", []), NIVEL_MODERADO
        )
        alteracoes_aplicadas.extend(alteracoes_moderado)
        resultado, alteracoes_moderado_remocoes = _aplicar_remocoes(
            resultado, regras.get(NIVEL_MODERADO, {}).get("remocoes", []), NIVEL_MODERADO
        )
        alteracoes_aplicadas.extend(alteracoes_moderado_remocoes)

    if nivel == NIVEL_AGRESSIVO:
        resultado, alteracoes_agressivo = _aplicar_substituicoes(
            resultado, regras.get(NIVEL_AGRESSIVO, {}).get("substituicoes", []), NIVEL_AGRESSIVO
        )
        alteracoes_aplicadas.extend(alteracoes_agressivo)
        resultado, alteracoes_agressivo_remocoes = _aplicar_remocoes(
            resultado, regras.get(NIVEL_AGRESSIVO, {}).get("remocoes", []), NIVEL_AGRESSIVO
        )
        alteracoes_aplicadas.extend(alteracoes_agressivo_remocoes)

    if nivel in (NIVEL_MODERADO, NIVEL_AGRESSIVO):
        # Substituições/remoções podem deixar espaços e pontuação soltos;
        # a limpeza conservadora final não é registrada como nova alteração
        # estrutural própria do nível moderado/agressivo, apenas normaliza.
        resultado, _ = normalizar_conservador(resultado, saudacoes_isoladas=[])

    texto_final = restaurar_termos(resultado, mapa_protegidos)

    encoding, fallback_utilizado = obter_encoding_info(modelo)
    tokens_originais = len(encoding.encode(texto_normalizado))
    tokens_compactados = len(encoding.encode(texto_final))

    avisos = [_AVISOS_POR_NIVEL[nivel], _AVISO_APROVACAO_HUMANA]

    compactacao_aplicada = tokens_compactados < tokens_originais

    if not compactacao_aplicada:
        texto_final = texto_normalizado
        tokens_compactados = tokens_originais
        avisos.append(
            "A compactação não reduziu a quantidade de tokens; o texto original foi mantido."
        )

    tokens_economizados = tokens_originais - tokens_compactados
    reducao_percentual = (
        round((tokens_economizados / tokens_originais) * 100, 2) if tokens_originais > 0 else 0.0
    )

    return ResultadoCompactacaoPrompt(
        texto_original=texto_normalizado,
        texto_compactado=texto_final,
        nivel=nivel,
        modelo=modelo,
        encoding=encoding.name,
        tokens_originais=tokens_originais,
        tokens_compactados=tokens_compactados,
        tokens_economizados=tokens_economizados,
        reducao_percentual=reducao_percentual,
        caracteres_originais=len(texto_normalizado),
        caracteres_compactados=len(texto_final),
        alteracoes_aplicadas=alteracoes_aplicadas,
        termos_protegidos=listar_termos_protegidos_encontrados(mapa_protegidos),
        avisos=avisos,
        risco=RISCO_POR_NIVEL[nivel],
        fallback_utilizado=fallback_utilizado,
        compactacao_aplicada=compactacao_aplicada,
    )
