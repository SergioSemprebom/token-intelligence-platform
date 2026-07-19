import pytest

from app.services.compression_comparator import comparar_niveis


def test_texto_vazio_levanta_erro() -> None:
    with pytest.raises(ValueError):
        comparar_niveis("")


def test_resultados_incluem_original_e_os_tres_niveis() -> None:
    resultado = comparar_niveis("Por favor, gostaria que você pudesse revisar isso.")

    niveis = [item["nivel"] for item in resultado["resultados"]]
    assert niveis == ["original", "conservador", "moderado", "agressivo"]


def test_recomendado_prefere_moderado_quando_ha_beneficio() -> None:
    texto = "Por favor, gostaria que você pudesse revisar detalhadamente o documento inteiro."

    resultado = comparar_niveis(texto)

    assert resultado["recomendado"] == "moderado"


def test_melhor_reducao_nao_e_selecionada_automaticamente_como_recomendada() -> None:
    texto = "Por favor, gostaria que você pudesse revisar detalhadamente o documento inteiro."

    resultado = comparar_niveis(texto)

    # O agressivo nunca é escolhido como recomendado só por reduzir mais,
    # a menos que nenhum outro nível traga benefício.
    if resultado["melhor_reducao"] == "agressivo":
        assert resultado["avisos"]


def test_sem_beneficio_em_nenhum_nivel_recomenda_nenhum() -> None:
    texto = "Analise o relatorio financeiro completo."

    resultado = comparar_niveis(texto)

    assert resultado["recomendado"] == "nenhum"
    assert resultado["melhor_reducao"] == "nenhum"


def test_cada_resultado_possui_risco_correspondente() -> None:
    resultado = comparar_niveis("Texto de exemplo para comparação entre níveis.")

    riscos_por_nivel = {item["nivel"]: item["risco"] for item in resultado["resultados"]}
    assert riscos_por_nivel["conservador"] == "baixo"
    assert riscos_por_nivel["moderado"] == "medio"
    assert riscos_por_nivel["agressivo"] == "alto"
