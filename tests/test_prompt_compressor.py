import pytest

from app.services.prompt_compressor import RISCO_POR_NIVEL, compactar_prompt


def test_texto_vazio_levanta_erro() -> None:
    with pytest.raises(ValueError):
        compactar_prompt("", nivel="conservador")

    with pytest.raises(ValueError):
        compactar_prompt("   ", nivel="conservador")


def test_nivel_invalido_levanta_erro() -> None:
    with pytest.raises(ValueError):
        compactar_prompt("Texto qualquer", nivel="inexistente")


@pytest.mark.parametrize("nivel", ["conservador", "moderado", "agressivo"])
def test_risco_corresponde_ao_nivel(nivel: str) -> None:
    resultado = compactar_prompt("Texto de exemplo para compactar", nivel=nivel)

    assert resultado.risco == RISCO_POR_NIVEL[nivel]
    assert resultado.nivel == nivel


def test_nivel_conservador_remove_espacos_e_pontuacao_duplicados() -> None:
    texto = "Isso   e  muito importante!!!  Confirme  ,  por favor."

    resultado = compactar_prompt(texto, nivel="conservador")

    assert "   " not in resultado.texto_compactado
    assert "!!!" not in resultado.texto_compactado
    assert resultado.compactacao_aplicada is True


def test_nivel_moderado_simplifica_expressoes_redundantes() -> None:
    texto = "Por favor, gostaria que você pudesse revisar detalhadamente o documento."

    resultado = compactar_prompt(texto, nivel="moderado")

    assert "gostaria que você pudesse" not in resultado.texto_compactado.lower()
    assert resultado.tokens_compactados < resultado.tokens_originais
    assert resultado.compactacao_aplicada is True


def test_nivel_agressivo_inclui_regras_do_moderado() -> None:
    texto = "Por favor, gostaria que você pudesse revisar o documento."

    resultado = compactar_prompt(texto, nivel="agressivo")

    assert "gostaria que você pudesse" not in resultado.texto_compactado.lower()


def test_preserva_numeros() -> None:
    texto = "Por favor, gostaria que você pudesse revisar os 42 itens da lista."

    resultado = compactar_prompt(texto, nivel="agressivo")

    assert "42" in resultado.texto_compactado


def test_preserva_datas() -> None:
    texto = "Por favor, gostaria que você pudesse entregar isso até 2026-07-19."

    resultado = compactar_prompt(texto, nivel="agressivo")

    assert "2026-07-19" in resultado.texto_compactado


def test_preserva_nomes_de_tabelas_e_identificadores_com_underscore() -> None:
    texto = (
        "Por favor, gostaria que você pudesse consultar a tabela analytics.f_processamentos "
        "e a coluna BITS_COUNT."
    )

    resultado = compactar_prompt(texto, nivel="agressivo")

    assert "analytics.f_processamentos" in resultado.texto_compactado
    assert "BITS_COUNT" in resultado.texto_compactado


def test_preserva_urls() -> None:
    texto = "Por favor, gostaria que você pudesse acessar https://exemplo.com/relatorio."

    resultado = compactar_prompt(texto, nivel="agressivo")

    assert "https://exemplo.com/relatorio" in resultado.texto_compactado


def test_preserva_blocos_de_codigo() -> None:
    texto = "Por favor, gostaria que você pudesse revisar este código:\n```SELECT * FROM tabela;```"

    resultado = compactar_prompt(texto, nivel="agressivo")

    assert "```SELECT * FROM tabela;```" in resultado.texto_compactado


def test_preserva_termos_protegidos_extras_informados_pelo_usuario() -> None:
    texto = "Por favor, gostaria que você pudesse revisar o projeto MeuProjetoEspecial."

    resultado = compactar_prompt(
        texto, nivel="agressivo", termos_protegidos=["MeuProjetoEspecial"]
    )

    assert "MeuProjetoEspecial" in resultado.texto_compactado


def test_compactacao_sem_economia_mantem_texto_original() -> None:
    texto = "Analise o relatorio financeiro completo."

    resultado = compactar_prompt(texto, nivel="conservador")

    assert resultado.compactacao_aplicada is False
    assert resultado.texto_compactado == resultado.texto_original
    assert resultado.tokens_economizados == 0
    assert resultado.reducao_percentual == 0.0


def test_economia_positiva_calcula_percentual_corretamente() -> None:
    texto = "Por favor, gostaria que você pudesse revisar detalhadamente o documento inteiro."

    resultado = compactar_prompt(texto, nivel="moderado")

    assert resultado.tokens_economizados == resultado.tokens_originais - resultado.tokens_compactados
    percentual_esperado = round(
        (resultado.tokens_economizados / resultado.tokens_originais) * 100, 2
    )
    assert resultado.reducao_percentual == percentual_esperado


def test_fallback_utilizado_para_modelo_desconhecido() -> None:
    resultado = compactar_prompt("Texto qualquer", nivel="conservador", modelo="modelo-inexistente-xyz")

    assert resultado.fallback_utilizado is True
    assert resultado.encoding == "o200k_base"


def test_avisos_incluem_alerta_de_aprovacao_humana() -> None:
    resultado = compactar_prompt("Texto de exemplo", nivel="agressivo")

    assert any("aprovação humana" in aviso.lower() for aviso in resultado.avisos)
    assert any("risco alto" in aviso.lower() for aviso in resultado.avisos)
