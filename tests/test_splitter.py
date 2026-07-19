import pytest

from app.core.splitter import dividir_texto_por_tokens


def test_texto_menor_que_limite_gera_um_unico_bloco() -> None:
    blocos = dividir_texto_por_tokens(texto="Ola mundo", limite_tokens=100)

    assert len(blocos) == 1
    assert blocos[0].indice == 0
    assert blocos[0].token_inicial == 0


def test_texto_maior_que_limite_gera_varios_blocos() -> None:
    texto = " ".join(f"palavra{i}" for i in range(200))

    blocos = dividir_texto_por_tokens(texto=texto, limite_tokens=20)

    assert len(blocos) > 1


def test_nenhum_bloco_ultrapassa_o_limite() -> None:
    texto = " ".join(f"palavra{i}" for i in range(200))
    limite = 15

    blocos = dividir_texto_por_tokens(texto=texto, limite_tokens=limite)

    assert all(bloco.quantidade_tokens <= limite for bloco in blocos)


def test_sobreposicao_valida_gera_intersecao_entre_blocos() -> None:
    texto = " ".join(f"palavra{i}" for i in range(200))

    blocos = dividir_texto_por_tokens(texto=texto, limite_tokens=20, sobreposicao=5)

    assert len(blocos) > 1
    assert blocos[1].token_inicial < blocos[0].token_final


def test_reconstrucao_sem_sobreposicao_preserva_o_texto() -> None:
    texto = "Este e um texto de teste para verificar a reconstrucao dos blocos de forma correta"

    blocos = dividir_texto_por_tokens(texto=texto, limite_tokens=5)
    texto_reconstruido = "".join(bloco.texto for bloco in blocos)

    assert texto_reconstruido == texto


def test_limite_zero_ou_negativo_levanta_erro() -> None:
    with pytest.raises(ValueError):
        dividir_texto_por_tokens(texto="Ola mundo", limite_tokens=0)

    with pytest.raises(ValueError):
        dividir_texto_por_tokens(texto="Ola mundo", limite_tokens=-1)


def test_sobreposicao_negativa_levanta_erro() -> None:
    with pytest.raises(ValueError):
        dividir_texto_por_tokens(texto="Ola mundo", limite_tokens=10, sobreposicao=-1)


def test_sobreposicao_maior_ou_igual_ao_limite_levanta_erro() -> None:
    with pytest.raises(ValueError):
        dividir_texto_por_tokens(texto="Ola mundo", limite_tokens=10, sobreposicao=10)

    with pytest.raises(ValueError):
        dividir_texto_por_tokens(texto="Ola mundo", limite_tokens=10, sobreposicao=11)


def test_texto_vazio_levanta_erro() -> None:
    with pytest.raises(ValueError):
        dividir_texto_por_tokens(texto="", limite_tokens=10)

    with pytest.raises(ValueError):
        dividir_texto_por_tokens(texto="   ", limite_tokens=10)
