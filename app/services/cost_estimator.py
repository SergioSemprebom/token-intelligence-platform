"""Serviço de estimativa de custos de uso de tokens."""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

CAMINHO_PRECOS_PADRAO = Path(__file__).resolve().parent.parent / "config" / "model_prices.json"

QUANTIZACAO_CUSTO = Decimal("0.000001")


@dataclass(frozen=True)
class ConfiguracaoPreco:
    """Preços por 1 milhão de tokens configurados para um modelo."""

    preco_entrada_por_1m: Decimal
    preco_saida_por_1m: Decimal


@dataclass(frozen=True)
class ResultadoEstimativaCusto:
    """Resultado da estimativa de custo de uso de tokens."""

    modelo: str
    tokens_entrada: int
    tokens_saida: int
    tokens_total: int
    custo_entrada: Decimal
    custo_saida: Decimal
    custo_total: Decimal


def carregar_precos_modelos(caminho: Path = CAMINHO_PRECOS_PADRAO) -> dict[str, ConfiguracaoPreco]:
    """
    Carrega as configurações de preços por modelo a partir do arquivo JSON.

    Os valores do arquivo são demonstrativos e podem ser atualizados sem
    necessidade de alterar o código-fonte.
    """
    conteudo = json.loads(caminho.read_text(encoding="utf-8"))
    modelos = conteudo.get("modelos", {})

    return {
        nome: ConfiguracaoPreco(
            preco_entrada_por_1m=Decimal(str(dados["preco_entrada_por_1m"])),
            preco_saida_por_1m=Decimal(str(dados["preco_saida_por_1m"])),
        )
        for nome, dados in modelos.items()
    }


def obter_aviso_precos(caminho: Path = CAMINHO_PRECOS_PADRAO) -> str:
    """Retorna o aviso sobre a natureza demonstrativa dos preços configurados."""
    conteudo = json.loads(caminho.read_text(encoding="utf-8"))
    return conteudo.get("_aviso", "")


def normalizar_nome_modelo(modelo: str) -> str:
    """Normaliza o nome de um modelo removendo espaços e convertendo para minúsculas."""
    return modelo.strip().lower()


def listar_modelos_disponiveis(caminho: Path = CAMINHO_PRECOS_PADRAO) -> list[str]:
    """Retorna a lista ordenada de modelos configurados em model_prices.json."""
    precos = carregar_precos_modelos(caminho)
    return sorted(precos.keys())


def obter_preco_modelo(modelo: str, caminho: Path = CAMINHO_PRECOS_PADRAO) -> ConfiguracaoPreco:
    """Retorna a configuração de preço de um modelo específico."""
    precos = carregar_precos_modelos(caminho)
    modelo_normalizado = normalizar_nome_modelo(modelo)
    precos_normalizados = {
        normalizar_nome_modelo(nome): preco for nome, preco in precos.items()
    }

    if modelo_normalizado not in precos_normalizados:
        raise ValueError(f"Modelo '{modelo}' não encontrado em model_prices.json.")

    return precos_normalizados[modelo_normalizado]


def estimar_custo(
    tokens_entrada: int,
    tokens_saida: int,
    preco_entrada_por_1m: Decimal,
    preco_saida_por_1m: Decimal,
    modelo: str,
) -> ResultadoEstimativaCusto:
    """
    Calcula o custo estimado de entrada, saída e total para um modelo.

    Utiliza Decimal em todo o cálculo para evitar imprecisões de
    arredondamento típicas de valores em ponto flutuante.
    """
    if tokens_entrada < 0 or tokens_saida < 0:
        raise ValueError("A quantidade de tokens não pode ser negativa.")

    if preco_entrada_por_1m < 0 or preco_saida_por_1m < 0:
        raise ValueError("Os preços não podem ser negativos.")

    um_milhao = Decimal("1000000")

    custo_entrada = (Decimal(tokens_entrada) / um_milhao * preco_entrada_por_1m).quantize(
        QUANTIZACAO_CUSTO
    )
    custo_saida = (Decimal(tokens_saida) / um_milhao * preco_saida_por_1m).quantize(
        QUANTIZACAO_CUSTO
    )

    return ResultadoEstimativaCusto(
        modelo=modelo,
        tokens_entrada=tokens_entrada,
        tokens_saida=tokens_saida,
        tokens_total=tokens_entrada + tokens_saida,
        custo_entrada=custo_entrada,
        custo_saida=custo_saida,
        custo_total=custo_entrada + custo_saida,
    )


def estimar_custo_por_modelo(
    tokens_entrada: int,
    tokens_saida: int,
    modelo: str,
    caminho: Path = CAMINHO_PRECOS_PADRAO,
) -> ResultadoEstimativaCusto:
    """Calcula o custo estimado buscando os preços do modelo no arquivo JSON."""
    modelo_normalizado = normalizar_nome_modelo(modelo)
    preco = obter_preco_modelo(modelo_normalizado, caminho)

    return estimar_custo(
        tokens_entrada=tokens_entrada,
        tokens_saida=tokens_saida,
        preco_entrada_por_1m=preco.preco_entrada_por_1m,
        preco_saida_por_1m=preco.preco_saida_por_1m,
        modelo=modelo_normalizado,
    )
