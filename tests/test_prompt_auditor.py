import pytest

from app.services.prompt_auditor import auditar_prompt


def test_texto_vazio_levanta_erro() -> None:
    with pytest.raises(ValueError):
        auditar_prompt("")

    with pytest.raises(ValueError):
        auditar_prompt("   ")


def test_auditoria_retorna_contagens_basicas() -> None:
    resultado = auditar_prompt("Primeira frase. Segunda frase.\nSegunda linha.", modelo="gpt-4o")

    assert resultado["tokens_originais"] > 0
    assert resultado["caracteres"] > 0
    assert resultado["palavras"] > 0
    assert resultado["linhas"] == 2
    assert resultado["frases"] >= 2
    assert "token_ids" not in resultado


def test_detecta_espacos_excessivos() -> None:
    resultado = auditar_prompt("Isso  tem  espacos duplicados")

    tipos = {problema["tipo"] for problema in resultado["problemas_encontrados"]}
    assert "espacos_excessivos" in tipos


def test_detecta_pontuacao_repetida() -> None:
    resultado = auditar_prompt("Isso e muito importante!!!")

    tipos = {problema["tipo"] for problema in resultado["problemas_encontrados"]}
    assert "pontuacao_repetida" in tipos


def test_detecta_palavras_duplicadas() -> None:
    resultado = auditar_prompt("Preciso preciso preciso disso rapido")

    tipos = {problema["tipo"] for problema in resultado["problemas_encontrados"]}
    assert "palavras_duplicadas" in tipos


def test_detecta_expressao_redundante() -> None:
    resultado = auditar_prompt("Gostaria que você pudesse revisar este texto.")

    tipos = {problema["tipo"] for problema in resultado["problemas_encontrados"]}
    assert "expressao_redundante" in tipos


def test_detecta_instrucao_repetida() -> None:
    frase = "Por favor revise cuidadosamente o documento inteiro"
    resultado = auditar_prompt(f"{frase}. {frase}.")

    tipos = {problema["tipo"] for problema in resultado["problemas_encontrados"]}
    assert "instrucao_repetida" in tipos


def test_nivel_desperdicio_baixo_sem_problemas() -> None:
    resultado = auditar_prompt("Texto limpo e direto sem problemas relevantes")

    assert resultado["nivel_desperdicio"] == "baixo"
    assert resultado["problemas_encontrados"] == []


def test_nivel_desperdicio_alto_com_muitos_problemas() -> None:
    texto = (
        "Por favor, gostaria que você pudesse. Preciso que você faça. Quero que você "
        "responda!!! Isso   tem   varios   espacos. palavra palavra repetida repetida "
        "muito muito. Poderia por favor me ajudar."
    )
    resultado = auditar_prompt(texto)

    assert resultado["nivel_desperdicio"] in {"medio", "alto"}
    assert resultado["recomendacoes"]


def test_fallback_utilizado_para_modelo_desconhecido() -> None:
    resultado = auditar_prompt("Texto qualquer", modelo="modelo-inexistente-xyz")

    assert resultado["fallback_utilizado"] is True
    assert resultado["encoding"] == "o200k_base"


def test_quantidade_termos_protegidos_conta_trechos_tecnicos() -> None:
    resultado = auditar_prompt("A tabela analytics.f_processamentos tem BITS_COUNT=32 e a data 2026-07-19.")

    assert resultado["quantidade_termos_protegidos"] > 0


def test_recomendacoes_sempre_presentes() -> None:
    resultado = auditar_prompt("Texto simples")

    assert isinstance(resultado["recomendacoes"], list)
    assert len(resultado["recomendacoes"]) > 0
