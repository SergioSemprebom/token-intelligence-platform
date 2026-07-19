import pytest

from app.services.model_comparator import comparar_modelos


def test_comparacao_entre_dois_encodings() -> None:
    resultado_gpt4o, resultado_gpt35 = comparar_modelos(
        texto="Ola mundo",
        modelos=["gpt-4o", "gpt-3.5-turbo"],
    )

    assert resultado_gpt4o.encoding_utilizado == "o200k_base"
    assert resultado_gpt35.encoding_utilizado == "cl100k_base"
    assert resultado_gpt4o.encoding_utilizado != resultado_gpt35.encoding_utilizado


def test_estrutura_do_resultado() -> None:
    resultados = comparar_modelos(texto="Ola mundo", modelos=["gpt-4o"])
    resultado = resultados[0]

    assert resultado.modelo_solicitado == "gpt-4o"
    assert resultado.tokens > 0
    assert resultado.caracteres == len("Ola mundo")
    assert resultado.palavras == 2
    assert resultado.bytes_utf8 == len("Ola mundo".encode("utf-8"))
    assert resultado.media_caracteres_por_token > 0
    assert resultado.fallback_utilizado is False


def test_modelo_desconhecido_usa_fallback() -> None:
    resultados = comparar_modelos(texto="Ola mundo", modelos=["modelo-inexistente"])
    resultado = resultados[0]

    assert resultado.encoding_utilizado == "o200k_base"
    assert resultado.fallback_utilizado is True


def test_texto_vazio_levanta_erro() -> None:
    with pytest.raises(ValueError):
        comparar_modelos(texto="", modelos=["gpt-4o"])

    with pytest.raises(ValueError):
        comparar_modelos(texto="   ", modelos=["gpt-4o"])


def test_nome_do_modelo_e_normalizado_com_strip_e_lower() -> None:
    resultados = comparar_modelos(texto="Ola mundo", modelos=["  GPT-4O  "])
    resultado = resultados[0]

    assert resultado.modelo_solicitado == "gpt-4o"
    assert resultado.encoding_utilizado == "o200k_base"
    assert resultado.fallback_utilizado is False


def test_normalizacao_nao_esconde_fallback_de_modelo_desconhecido() -> None:
    resultados = comparar_modelos(texto="Ola mundo", modelos=["  Modelo-Inexistente  "])
    resultado = resultados[0]

    assert resultado.modelo_solicitado == "modelo-inexistente"
    assert resultado.encoding_utilizado == "o200k_base"
    assert resultado.fallback_utilizado is True
