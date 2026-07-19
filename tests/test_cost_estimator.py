from decimal import Decimal

import pytest

from app.services.cost_estimator import (
    ResultadoEstimativaCusto,
    estimar_custo,
    estimar_custo_por_modelo,
    listar_modelos_disponiveis,
    normalizar_nome_modelo,
)


def test_calculo_do_custo_de_entrada() -> None:
    resultado = estimar_custo(
        tokens_entrada=1_000_000,
        tokens_saida=0,
        preco_entrada_por_1m=Decimal("5.00"),
        preco_saida_por_1m=Decimal("15.00"),
        modelo="gpt-4o",
    )

    assert resultado.custo_entrada == Decimal("5.000000")
    assert resultado.custo_saida == Decimal("0.000000")


def test_calculo_do_custo_de_saida() -> None:
    resultado = estimar_custo(
        tokens_entrada=0,
        tokens_saida=1_000_000,
        preco_entrada_por_1m=Decimal("5.00"),
        preco_saida_por_1m=Decimal("15.00"),
        modelo="gpt-4o",
    )

    assert resultado.custo_entrada == Decimal("0.000000")
    assert resultado.custo_saida == Decimal("15.000000")


def test_calculo_do_custo_total() -> None:
    resultado = estimar_custo(
        tokens_entrada=1_000_000,
        tokens_saida=1_000_000,
        preco_entrada_por_1m=Decimal("5.00"),
        preco_saida_por_1m=Decimal("15.00"),
        modelo="gpt-4o",
    )

    assert resultado.custo_total == Decimal("20.000000")
    assert resultado.custo_total == resultado.custo_entrada + resultado.custo_saida


def test_zero_tokens_gera_custo_zero() -> None:
    resultado = estimar_custo(
        tokens_entrada=0,
        tokens_saida=0,
        preco_entrada_por_1m=Decimal("5.00"),
        preco_saida_por_1m=Decimal("15.00"),
        modelo="gpt-4o",
    )

    assert resultado.custo_total == Decimal("0.000000")
    assert resultado.tokens_total == 0


def test_tokens_negativos_sao_rejeitados() -> None:
    with pytest.raises(ValueError):
        estimar_custo(
            tokens_entrada=-1,
            tokens_saida=0,
            preco_entrada_por_1m=Decimal("5.00"),
            preco_saida_por_1m=Decimal("15.00"),
            modelo="gpt-4o",
        )

    with pytest.raises(ValueError):
        estimar_custo(
            tokens_entrada=0,
            tokens_saida=-1,
            preco_entrada_por_1m=Decimal("5.00"),
            preco_saida_por_1m=Decimal("15.00"),
            modelo="gpt-4o",
        )


def test_precos_negativos_sao_rejeitados() -> None:
    with pytest.raises(ValueError):
        estimar_custo(
            tokens_entrada=100,
            tokens_saida=100,
            preco_entrada_por_1m=Decimal("-1"),
            preco_saida_por_1m=Decimal("15.00"),
            modelo="gpt-4o",
        )


def test_modelo_inexistente_no_json_levanta_erro() -> None:
    with pytest.raises(ValueError):
        estimar_custo_por_modelo(
            tokens_entrada=100,
            tokens_saida=100,
            modelo="modelo-que-nao-existe",
        )


def test_precisao_com_decimal() -> None:
    resultado = estimar_custo(
        tokens_entrada=1234,
        tokens_saida=5678,
        preco_entrada_por_1m=Decimal("2.50"),
        preco_saida_por_1m=Decimal("7.50"),
        modelo="gpt-4o",
    )

    assert isinstance(resultado.custo_entrada, Decimal)
    assert isinstance(resultado.custo_saida, Decimal)
    assert isinstance(resultado.custo_total, Decimal)


def test_estimar_custo_por_modelo_utiliza_precos_do_json() -> None:
    resultado = estimar_custo_por_modelo(
        tokens_entrada=1_000_000,
        tokens_saida=1_000_000,
        modelo="gpt-4o",
    )

    assert isinstance(resultado, ResultadoEstimativaCusto)
    assert resultado.modelo == "gpt-4o"
    assert resultado.custo_total > 0


def test_normalizar_nome_modelo_remove_espacos_e_minusculiza() -> None:
    assert normalizar_nome_modelo("  GPT-4O  ") == "gpt-4o"


def test_listar_modelos_disponiveis_retorna_nomes_ordenados() -> None:
    modelos = listar_modelos_disponiveis()

    assert modelos == sorted(modelos)
    assert "gpt-4o" in modelos
    assert "gpt-4o-mini" in modelos
    assert "gpt-3.5-turbo" in modelos


def test_estimar_custo_por_modelo_aceita_nome_com_espacos_e_maiusculas() -> None:
    resultado = estimar_custo_por_modelo(
        tokens_entrada=1_000_000,
        tokens_saida=1_000_000,
        modelo="  GPT-4O  ",
    )

    assert resultado.modelo == "gpt-4o"
    assert resultado.custo_total > 0
