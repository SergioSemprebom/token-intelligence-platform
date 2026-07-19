import pytest

from app.cli.menu import (
    acao_auditar_prompt,
    acao_compactar_prompt,
    acao_comparar_compactacao,
    acao_estimar_custo,
    ler_confirmacao,
    ler_inteiro,
    ler_modelo_custo,
    ler_nivel_compactacao,
    ler_termos_protegidos_extra,
    ler_texto_multilinha,
)


def test_ler_texto_multilinha_junta_varias_linhas(monkeypatch: pytest.MonkeyPatch) -> None:
    entradas = iter(["primeira linha", "segunda linha", "FIM"])
    monkeypatch.setattr("builtins.input", lambda: next(entradas))

    resultado = ler_texto_multilinha()

    assert resultado == "primeira linha\nsegunda linha"


def test_ler_texto_multilinha_com_texto_unico(monkeypatch: pytest.MonkeyPatch) -> None:
    entradas = iter(["Ola mundo", "FIM"])
    monkeypatch.setattr("builtins.input", lambda: next(entradas))

    resultado = ler_texto_multilinha()

    assert resultado == "Ola mundo"


def test_ler_texto_multilinha_sem_conteudo_retorna_vazio(monkeypatch: pytest.MonkeyPatch) -> None:
    entradas = iter(["FIM"])
    monkeypatch.setattr("builtins.input", lambda: next(entradas))

    resultado = ler_texto_multilinha()

    assert resultado == ""


def test_ler_texto_multilinha_ignora_linhas_em_branco_no_meio(monkeypatch: pytest.MonkeyPatch) -> None:
    entradas = iter(["linha 1", "", "linha 3", "FIM"])
    monkeypatch.setattr("builtins.input", lambda: next(entradas))

    resultado = ler_texto_multilinha()

    assert resultado == "linha 1\n\nlinha 3"


def test_ler_inteiro_reincide_apos_entrada_invalida(monkeypatch: pytest.MonkeyPatch) -> None:
    entradas = iter(["abc", "-1", "5"])
    monkeypatch.setattr("builtins.input", lambda _: next(entradas))

    resultado = ler_inteiro("Valor: ", minimo=0)

    assert resultado == 5


def test_ler_confirmacao_aceita_variacoes_de_sim(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("builtins.input", lambda _: "s")
    assert ler_confirmacao("Confirma?") is True

    monkeypatch.setattr("builtins.input", lambda _: "n")
    assert ler_confirmacao("Confirma?") is False


MODELOS_DISPONIVEIS = ["gpt-3.5-turbo", "gpt-4o", "gpt-4o-mini"]


def test_ler_modelo_custo_seleciona_por_numero(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("builtins.input", lambda _: "2")

    resultado = ler_modelo_custo(MODELOS_DISPONIVEIS)

    assert resultado == "gpt-4o"


def test_ler_modelo_custo_aceita_nome_digitado_manualmente(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("builtins.input", lambda _: "outro-modelo")

    resultado = ler_modelo_custo(MODELOS_DISPONIVEIS)

    assert resultado == "outro-modelo"


def test_ler_modelo_custo_normaliza_nome_com_strip_e_lower(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("builtins.input", lambda _: "  GPT-4O  ")

    resultado = ler_modelo_custo(MODELOS_DISPONIVEIS)

    assert resultado == "gpt-4o"


def test_ler_modelo_custo_rejeita_texto_multilinha(monkeypatch: pytest.MonkeyPatch) -> None:
    entradas = iter(["primeira linha\nsegunda linha", "gpt-4o"])
    monkeypatch.setattr("builtins.input", lambda _: next(entradas))

    resultado = ler_modelo_custo(MODELOS_DISPONIVEIS)

    assert resultado == "gpt-4o"


def test_ler_modelo_custo_reincide_com_entrada_vazia(monkeypatch: pytest.MonkeyPatch) -> None:
    entradas = iter(["", "gpt-4o"])
    monkeypatch.setattr("builtins.input", lambda _: next(entradas))

    resultado = ler_modelo_custo(MODELOS_DISPONIVEIS)

    assert resultado == "gpt-4o"


def test_ler_modelo_custo_reincide_com_numero_fora_do_intervalo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entradas = iter(["99", "1"])
    monkeypatch.setattr("builtins.input", lambda _: next(entradas))

    resultado = ler_modelo_custo(MODELOS_DISPONIVEIS)

    assert resultado == "gpt-3.5-turbo"


def test_acao_estimar_custo_exibe_aviso_com_quebra_de_linha_e_lista_modelos(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    entradas = iter(["100", "50", "2"])
    monkeypatch.setattr("builtins.input", lambda _: next(entradas))

    acao_estimar_custo()

    saida = capsys.readouterr().out

    assert "\n\n" in saida.split("Modelos disponíveis", maxsplit=1)[0]
    assert "gpt-4o" in saida
    assert "modelo: gpt-4o" in saida


def test_acao_estimar_custo_mantem_usuario_na_operacao_apos_modelo_invalido(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    entradas = iter(["100", "50", "modelo-que-nao-existe", "gpt-4o"])
    monkeypatch.setattr("builtins.input", lambda _: next(entradas))

    acao_estimar_custo()

    saida = capsys.readouterr().out

    assert "Erro:" in saida
    assert "modelo: gpt-4o" in saida


def test_ler_termos_protegidos_extra_ignora_entrada_vazia(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("builtins.input", lambda *_: "")

    assert ler_termos_protegidos_extra() == []


def test_ler_termos_protegidos_extra_separa_por_virgula(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("builtins.input", lambda *_: " TermoA , TermoB ,, ")

    assert ler_termos_protegidos_extra() == ["TermoA", "TermoB"]


def test_ler_nivel_compactacao_padrao_moderado(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("builtins.input", lambda *_: "")

    assert ler_nivel_compactacao() == "moderado"


def test_ler_nivel_compactacao_reincide_apos_valor_invalido(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entradas = iter(["invalido", "agressivo"])
    monkeypatch.setattr("builtins.input", lambda *_: next(entradas))

    assert ler_nivel_compactacao() == "agressivo"


def test_acao_auditar_prompt_exibe_diagnostico(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    entradas = iter(
        ["Por favor, gostaria que você pudesse revisar isso.", "FIM", "", ""]
    )
    monkeypatch.setattr("builtins.input", lambda *_: next(entradas))

    acao_auditar_prompt()

    saida = capsys.readouterr().out

    assert "tokens_originais" in saida
    assert "nivel_desperdicio" in saida
    assert "Recomendações" in saida


def test_acao_compactar_prompt_exibe_resultado_e_respeita_aprovacao(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    entradas = iter(
        [
            "Por favor, gostaria que você pudesse revisar detalhadamente o documento inteiro.",
            "FIM",
            "",
            "",
            "",
            "s",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda *_: next(entradas))

    acao_compactar_prompt()

    saida = capsys.readouterr().out

    assert "Texto compactado (sugestão)" in saida
    assert "tokens_originais" in saida
    assert "Aprovado nesta sessão" in saida
    assert "NÃO foi sobrescrito automaticamente" in saida


def test_acao_compactar_prompt_sem_aprovacao_mantem_original(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    entradas = iter(
        [
            "Por favor, gostaria que você pudesse revisar detalhadamente o documento inteiro.",
            "FIM",
            "",
            "",
            "",
            "n",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda *_: next(entradas))

    acao_compactar_prompt()

    saida = capsys.readouterr().out

    assert "Não aprovado" in saida


def test_acao_comparar_compactacao_exibe_ranking(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    entradas = iter(
        ["Por favor, gostaria que você pudesse revisar isso.", "FIM", "", ""]
    )
    monkeypatch.setattr("builtins.input", lambda *_: next(entradas))

    acao_comparar_compactacao()

    saida = capsys.readouterr().out

    assert "melhor_reducao" in saida
    assert "recomendado" in saida
