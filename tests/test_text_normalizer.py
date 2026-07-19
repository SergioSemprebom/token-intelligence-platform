from app.core.text_normalizer import (
    normalizar_conservador,
    remover_espaco_antes_fecha_parenteses,
    remover_espaco_antes_pontuacao,
    remover_espaco_apos_abre_parenteses,
    remover_espacos_duplicados,
    remover_linhas_repetidas_consecutivas,
    remover_linhas_vazias_excessivas,
    remover_palavras_consecutivas_duplicadas,
    remover_pontuacao_repetida,
    remover_saudacoes_isoladas,
)


def test_texto_vazio_nao_gera_alteracoes() -> None:
    resultado, alteracoes = normalizar_conservador("")

    assert resultado == ""
    assert alteracoes == []


def test_remove_espacos_duplicados() -> None:
    resultado, quantidade = remover_espacos_duplicados("Ola    mundo")

    assert resultado == "Ola mundo"
    assert quantidade == 1


def test_remove_linhas_vazias_excessivas() -> None:
    resultado, quantidade = remover_linhas_vazias_excessivas("linha1\n\n\n\nlinha2")

    assert resultado == "linha1\n\nlinha2"
    assert quantidade == 1


def test_remove_pontuacao_repetida() -> None:
    resultado, quantidade = remover_pontuacao_repetida("Isso e muito importante!!! Certo??")

    assert resultado == "Isso e muito importante! Certo?"
    assert quantidade == 2


def test_remove_palavras_consecutivas_duplicadas() -> None:
    resultado, quantidade = remover_palavras_consecutivas_duplicadas("o o carro carro esta pronto")

    assert resultado == "o carro esta pronto"
    assert quantidade == 2


def test_remove_espaco_antes_pontuacao() -> None:
    resultado, quantidade = remover_espaco_antes_pontuacao("Ola , mundo !")

    assert resultado == "Ola, mundo!"
    assert quantidade == 2


def test_remove_espaco_apos_abre_parenteses() -> None:
    resultado, quantidade = remover_espaco_apos_abre_parenteses("texto (  entre parenteses)")

    assert resultado == "texto (entre parenteses)"
    assert quantidade == 1


def test_remove_espaco_antes_fecha_parenteses() -> None:
    resultado, quantidade = remover_espaco_antes_fecha_parenteses("texto (entre parenteses  )")

    assert resultado == "texto (entre parenteses)"
    assert quantidade == 1


def test_remove_linhas_repetidas_consecutivas() -> None:
    resultado, quantidade = remover_linhas_repetidas_consecutivas("linha repetida\nlinha repetida\noutra linha")

    assert resultado == "linha repetida\noutra linha"
    assert quantidade == 1


def test_remove_saudacoes_isoladas() -> None:
    texto = "Ola\nPreciso de ajuda com o relatorio\nBom dia"
    resultado, quantidade = remover_saudacoes_isoladas(texto, ["ola", "bom dia"])

    assert resultado == "Preciso de ajuda com o relatorio"
    assert quantidade == 2


def test_remove_saudacoes_isoladas_sem_lista_nao_altera_texto() -> None:
    resultado, quantidade = remover_saudacoes_isoladas("Ola\ntexto", [])

    assert resultado == "Ola\ntexto"
    assert quantidade == 0


def test_normalizar_conservador_aplica_todas_as_regras() -> None:
    texto = "Ola\n\n\nPor   favor,  analise analise isso !!!  ( sim )"

    resultado, alteracoes = normalizar_conservador(texto, saudacoes_isoladas=["ola"])

    assert "  " not in resultado
    assert "!!!" not in resultado
    assert "analise analise" not in resultado
    tipos = {alteracao.tipo for alteracao in alteracoes}
    assert "espacos_duplicados" in tipos
    assert "pontuacao_repetida" in tipos
    assert "palavras_consecutivas_duplicadas" in tipos
    assert "saudacao_isolada" in tipos
