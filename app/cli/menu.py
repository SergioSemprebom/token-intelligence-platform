"""Menu interativo de terminal da Token Intelligence Platform."""

from __future__ import annotations

from app.core.splitter import dividir_texto_por_tokens
from app.core.tokenizer import analisar_texto
from app.services.compression_comparator import comparar_niveis
from app.services.cost_estimator import (
    estimar_custo_por_modelo,
    listar_modelos_disponiveis,
    obter_aviso_precos,
)
from app.services.model_comparator import comparar_modelos
from app.services.prompt_auditor import auditar_prompt
from app.services.prompt_compressor import NIVEIS_VALIDOS, compactar_prompt

OPCAO_ANALISAR_TEXTO = 1
OPCAO_ESTIMAR_CUSTO = 2
OPCAO_DIVIDIR_TEXTO = 3
OPCAO_COMPARAR_MODELOS = 4
OPCAO_AUDITAR_PROMPT = 5
OPCAO_COMPACTAR_PROMPT = 6
OPCAO_COMPARAR_COMPACTACAO = 7
OPCAO_SAIR = 8


def ler_texto_multilinha() -> str:
    """
    Lê várias linhas digitadas pelo usuário até encontrar uma linha
    contendo apenas "FIM", e retorna o texto completo digitado.
    """
    print("Digite ou cole o texto desejado.")
    print("Para finalizar, digite uma linha contendo apenas: FIM\n")

    linhas: list[str] = []

    while True:
        linha = input()

        if linha.strip() == "FIM":
            break

        linhas.append(linha)

    return "\n".join(linhas)


def ler_inteiro(mensagem: str, minimo: int = 0) -> int:
    """Solicita um número inteiro ao usuário, validando a entrada até ser aceitável."""
    while True:
        entrada = input(mensagem).strip()

        try:
            valor = int(entrada)
        except ValueError:
            print("Entrada inválida. Informe um número inteiro.")
            continue

        if valor < minimo:
            print(f"Informe um número inteiro maior ou igual a {minimo}.")
            continue

        return valor


def ler_confirmacao(mensagem: str) -> bool:
    """Solicita uma confirmação sim/não ao usuário."""
    resposta = input(f"{mensagem} (s/n): ").strip().lower()
    return resposta in {"s", "sim"}


def exibir_menu() -> None:
    """Exibe as opções do menu principal."""
    print("\n" + "=" * 50)
    print("Token Intelligence Platform")
    print("=" * 50)
    print("1. Analisar texto")
    print("2. Estimar custo")
    print("3. Dividir texto por tokens")
    print("4. Comparar modelos")
    print("5. Auditar prompt")
    print("6. Compactar prompt")
    print("7. Comparar níveis de compactação")
    print("8. Sair")


def ler_opcao_menu() -> int:
    """Lê e valida a opção escolhida pelo usuário no menu principal."""
    return ler_inteiro("\nEscolha uma opção: ", minimo=OPCAO_ANALISAR_TEXTO)


def acao_analisar_texto() -> None:
    """Executa a análise de texto solicitada pelo usuário."""
    texto = ler_texto_multilinha()
    modelo = input("Modelo (padrão: gpt-4o): ").strip() or "gpt-4o"
    mostrar_ids = ler_confirmacao("Deseja exibir os token_ids?")

    resultado = analisar_texto(texto=texto, modelo=modelo, incluir_token_ids=mostrar_ids)

    print("\nResultado da análise")
    print("-" * 50)
    for chave, valor in resultado.items():
        print(f"{chave}: {valor}")


def ler_modelo_custo(modelos_disponiveis: list[str]) -> str:
    """
    Solicita o modelo para a estimativa de custo.

    Permite escolher pelo número exibido na lista de modelos disponíveis
    ou digitar o nome do modelo manualmente. Rejeita entradas com mais
    de uma linha, para evitar que um texto colado por engano seja
    interpretado como nome de modelo.
    """
    print("Modelos disponíveis:")
    for indice, nome in enumerate(modelos_disponiveis, start=1):
        print(f"  {indice}. {nome}")

    while True:
        print(
            "\nEscolha o número do modelo acima ou digite o nome do modelo "
            "(conforme model_prices.json):"
        )
        entrada = input("> ")

        if "\n" in entrada or "\r" in entrada:
            print("Entrada inválida: não é permitido colar texto com múltiplas linhas.")
            continue

        entrada_normalizada = entrada.strip()

        if not entrada_normalizada:
            print("Informe um número ou o nome de um modelo.")
            continue

        if entrada_normalizada.isdigit():
            indice = int(entrada_normalizada)
            if 1 <= indice <= len(modelos_disponiveis):
                return modelos_disponiveis[indice - 1]
            print(f"Informe um número entre 1 e {len(modelos_disponiveis)}.")
            continue

        return entrada_normalizada.lower()


def acao_estimar_custo() -> None:
    """Executa a estimativa de custo solicitada pelo usuário."""
    aviso = obter_aviso_precos()
    if aviso:
        print(f"\nAviso: {aviso}\n")

    modelos_disponiveis = listar_modelos_disponiveis()

    if not modelos_disponiveis:
        print("Nenhum modelo configurado em model_prices.json.")
        return

    tokens_entrada = ler_inteiro("Quantidade de tokens de entrada: ", minimo=0)
    tokens_saida = ler_inteiro("Quantidade de tokens de saída: ", minimo=0)

    while True:
        modelo = ler_modelo_custo(modelos_disponiveis)

        try:
            resultado = estimar_custo_por_modelo(
                tokens_entrada=tokens_entrada,
                tokens_saida=tokens_saida,
                modelo=modelo,
            )
        except ValueError as erro:
            print(f"\nErro: {erro}")
            continue

        break

    print("\nResultado da estimativa de custo")
    print("-" * 50)
    print(f"modelo: {resultado.modelo}")
    print(f"tokens_entrada: {resultado.tokens_entrada}")
    print(f"tokens_saida: {resultado.tokens_saida}")
    print(f"tokens_total: {resultado.tokens_total}")
    print(f"custo_entrada: {resultado.custo_entrada}")
    print(f"custo_saida: {resultado.custo_saida}")
    print(f"custo_total: {resultado.custo_total}")


def acao_dividir_texto() -> None:
    """Executa a divisão de texto por tokens solicitada pelo usuário."""
    texto = ler_texto_multilinha()
    modelo = input("Modelo (padrão: gpt-4o): ").strip() or "gpt-4o"
    limite_tokens = ler_inteiro("Limite máximo de tokens por bloco: ", minimo=1)
    sobreposicao = ler_inteiro("Sobreposição em tokens (padrão 0): ", minimo=0)

    blocos = dividir_texto_por_tokens(
        texto=texto,
        modelo=modelo,
        limite_tokens=limite_tokens,
        sobreposicao=sobreposicao,
    )

    print(f"\nTexto dividido em {len(blocos)} bloco(s)")
    print("-" * 50)
    for bloco in blocos:
        print(
            f"bloco {bloco.indice}: tokens={bloco.quantidade_tokens} "
            f"(inicio={bloco.token_inicial}, fim={bloco.token_final})"
        )
        print(bloco.texto)
        print("-" * 50)


def acao_comparar_modelos() -> None:
    """Executa a comparação de tokenização entre modelos solicitada pelo usuário."""
    texto = ler_texto_multilinha()
    modelos_entrada = input("Informe os modelos separados por vírgula: ").strip()
    modelos = [modelo.strip() for modelo in modelos_entrada.split(",") if modelo.strip()]

    if not modelos:
        print("Nenhum modelo informado.")
        return

    resultados = comparar_modelos(texto=texto, modelos=modelos)

    print("\nResultado da comparação")
    print("-" * 50)
    for resultado in resultados:
        print(f"modelo solicitado: {resultado.modelo_solicitado}")
        print(f"encoding utilizado: {resultado.encoding_utilizado}")
        print(f"tokens: {resultado.tokens}")
        print(f"caracteres: {resultado.caracteres}")
        print(f"palavras: {resultado.palavras}")
        print(f"bytes_utf8: {resultado.bytes_utf8}")
        print(f"media_caracteres_por_token: {resultado.media_caracteres_por_token}")
        if resultado.fallback_utilizado:
            print("aviso: modelo não reconhecido, foi utilizado fallback para o200k_base")
        print("-" * 50)


def ler_termos_protegidos_extra() -> list[str]:
    """Lê termos protegidos adicionais, informados pelo usuário, separados por vírgula."""
    entrada = input(
        "Termos protegidos adicionais, separados por vírgula (opcional): "
    ).strip()
    return [termo.strip() for termo in entrada.split(",") if termo.strip()]


def ler_nivel_compactacao() -> str:
    """Solicita e valida o nível de compactação escolhido pelo usuário."""
    niveis_ordenados = sorted(NIVEIS_VALIDOS, key=lambda nivel: {"conservador": 0, "moderado": 1, "agressivo": 2}[nivel])

    while True:
        print("Níveis disponíveis: " + ", ".join(niveis_ordenados))
        entrada = input("Escolha o nível de compactação (padrão: moderado): ").strip().lower()

        if not entrada:
            return "moderado"

        if entrada in NIVEIS_VALIDOS:
            if entrada == "agressivo":
                print(
                    "Aviso: o nível agressivo tem risco alto e pode alterar o significado "
                    "do texto. Revise cuidadosamente antes de aprovar."
                )
            return entrada

        print(f"Nível inválido. Escolha entre: {', '.join(niveis_ordenados)}.")


def acao_auditar_prompt() -> None:
    """Executa a auditoria de um prompt, apenas diagnosticando (sem alterá-lo)."""
    texto = ler_texto_multilinha()
    modelo = input("Modelo (padrão: gpt-4o): ").strip() or "gpt-4o"
    termos_protegidos = ler_termos_protegidos_extra()

    resultado = auditar_prompt(texto=texto, modelo=modelo, termos_protegidos=termos_protegidos)

    print("\nResultado da auditoria")
    print("-" * 50)
    print(f"tokens_originais: {resultado['tokens_originais']}")
    print(f"caracteres: {resultado['caracteres']}")
    print(f"palavras: {resultado['palavras']}")
    print(f"linhas: {resultado['linhas']}")
    print(f"frases: {resultado['frases']}")
    print(f"quantidade_termos_protegidos: {resultado['quantidade_termos_protegidos']}")
    print(f"nivel_desperdicio: {resultado['nivel_desperdicio']}")

    print("\nProblemas encontrados:")
    if not resultado["problemas_encontrados"]:
        print("  Nenhum problema relevante encontrado.")
    for problema in resultado["problemas_encontrados"]:
        print(
            f"  - [{problema['tipo']}] '{problema['trecho']}' "
            f"({problema['ocorrencias']}x) -> {problema['sugestao']}"
        )

    print("\nRecomendações:")
    for recomendacao in resultado["recomendacoes"]:
        print(f"  - {recomendacao}")


def acao_compactar_prompt() -> None:
    """Executa a compactação de um prompt, sempre exigindo aprovação humana."""
    texto = ler_texto_multilinha()
    modelo = input("Modelo (padrão: gpt-4o): ").strip() or "gpt-4o"
    nivel = ler_nivel_compactacao()
    termos_protegidos = ler_termos_protegidos_extra()

    resultado = compactar_prompt(
        texto=texto, nivel=nivel, modelo=modelo, termos_protegidos=termos_protegidos
    )

    print("\nTexto original")
    print("-" * 50)
    print(resultado.texto_original)

    print("\nTexto compactado (sugestão)")
    print("-" * 50)
    print(resultado.texto_compactado)

    print("\nResumo")
    print("-" * 50)
    print(f"nivel: {resultado.nivel} (risco: {resultado.risco})")
    print(f"tokens_originais: {resultado.tokens_originais}")
    print(f"tokens_compactados: {resultado.tokens_compactados}")
    print(f"tokens_economizados: {resultado.tokens_economizados}")
    print(f"reducao_percentual: {resultado.reducao_percentual}%")
    print(f"compactacao_aplicada: {resultado.compactacao_aplicada}")
    print(f"termos_protegidos: {resultado.termos_protegidos}")

    print("\nAlterações aplicadas:")
    if not resultado.alteracoes_aplicadas:
        print("  Nenhuma alteração aplicada.")
    for alteracao in resultado.alteracoes_aplicadas:
        print(f"  - {alteracao}")

    print("\nAvisos:")
    for aviso in resultado.avisos:
        print(f"  - {aviso}")

    aprovado = ler_confirmacao(
        "\nVocê aprova o uso do texto compactado no lugar do original?"
    )
    if aprovado:
        print(
            "Aprovado nesta sessão. O texto original NÃO foi sobrescrito automaticamente: "
            "copie o texto compactado acima manualmente onde desejar utilizá-lo."
        )
    else:
        print("Não aprovado. O texto original permanece inalterado.")


def acao_comparar_compactacao() -> None:
    """Compara os três níveis de compactação para o mesmo texto."""
    texto = ler_texto_multilinha()
    modelo = input("Modelo (padrão: gpt-4o): ").strip() or "gpt-4o"
    termos_protegidos = ler_termos_protegidos_extra()

    resultado = comparar_niveis(texto=texto, modelo=modelo, termos_protegidos=termos_protegidos)

    print("\nComparação entre níveis de compactação")
    print("-" * 50)
    print(f"tokens_originais: {resultado['tokens_originais']}")
    for item in resultado["resultados"]:
        print(
            f"  {item['nivel']:<12} tokens={item['tokens']:<6} "
            f"economizados={item['tokens_economizados']:<6} "
            f"reducao={item['reducao_percentual']}% risco={item['risco']} "
            f"aplicada={item['compactacao_aplicada']}"
        )

    print(f"\nmelhor_reducao: {resultado['melhor_reducao']}")
    print(f"recomendado: {resultado['recomendado']}")

    if resultado["avisos"]:
        print("\nAvisos:")
        for aviso in resultado["avisos"]:
            print(f"  - {aviso}")


ACOES = {
    OPCAO_ANALISAR_TEXTO: acao_analisar_texto,
    OPCAO_ESTIMAR_CUSTO: acao_estimar_custo,
    OPCAO_DIVIDIR_TEXTO: acao_dividir_texto,
    OPCAO_COMPARAR_MODELOS: acao_comparar_modelos,
    OPCAO_AUDITAR_PROMPT: acao_auditar_prompt,
    OPCAO_COMPACTAR_PROMPT: acao_compactar_prompt,
    OPCAO_COMPARAR_COMPACTACAO: acao_comparar_compactacao,
}


def iniciar_menu() -> None:
    """Inicia o laço principal do menu interativo."""
    while True:
        exibir_menu()
        opcao = ler_opcao_menu()

        if opcao == OPCAO_SAIR:
            print("\nEncerrando a Token Intelligence Platform.")
            return

        acao = ACOES.get(opcao)

        if acao is None:
            print("\nOpção inválida. Escolha um número entre 1 e 8.")
            continue

        try:
            acao()
        except ValueError as erro:
            print(f"\nErro de validação: {erro}")
        except Exception as erro:
            print(f"\nErro inesperado: {erro}")
