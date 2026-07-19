import pytest

from app.core.tokenizer import analisar_texto, obter_encoding_info


def test_analisar_texto_retorna_metricas_basicas() -> None:
    resultado = analisar_texto(texto="Ola mundo")

    assert resultado["caracteres"] == len("Ola mundo")
    assert resultado["palavras"] == 2
    assert resultado["bytes_utf8"] == len("Ola mundo".encode("utf-8"))
    assert resultado["tokens"] > 0
    assert resultado["media_caracteres_por_token"] > 0
    assert resultado["tempo_processamento_ms"] >= 0


def test_analisar_texto_nao_inclui_token_ids_por_padrao() -> None:
    resultado = analisar_texto(texto="Ola mundo")

    assert "token_ids" not in resultado


def test_analisar_texto_inclui_token_ids_quando_solicitado() -> None:
    resultado = analisar_texto(texto="Ola mundo", incluir_token_ids=True)

    assert "token_ids" in resultado
    assert isinstance(resultado["token_ids"], list)
    assert len(resultado["token_ids"]) == resultado["tokens"]


def test_analisar_texto_com_texto_vazio_levanta_erro() -> None:
    with pytest.raises(ValueError):
        analisar_texto(texto="")


def test_analisar_texto_com_texto_apenas_espacos_levanta_erro() -> None:
    with pytest.raises(ValueError):
        analisar_texto(texto="   ")


def test_analisar_texto_com_modelo_desconhecido_usa_encoding_padrao() -> None:
    resultado = analisar_texto(texto="Ola mundo", modelo="modelo-inexistente")

    assert resultado["encoding"] == "o200k_base"


def test_media_caracteres_por_token_calculada_corretamente() -> None:
    resultado = analisar_texto(texto="Ola mundo")

    media_esperada = round(resultado["caracteres"] / resultado["tokens"], 2)
    assert resultado["media_caracteres_por_token"] == media_esperada


def test_obter_encoding_info_com_modelo_conhecido_nao_indica_fallback() -> None:
    _, fallback_utilizado = obter_encoding_info("gpt-4o")

    assert fallback_utilizado is False


def test_obter_encoding_info_identifica_fallback_para_modelo_desconhecido() -> None:
    encoding, fallback_utilizado = obter_encoding_info("modelo-inexistente")

    assert fallback_utilizado is True
    assert encoding.name == "o200k_base"
