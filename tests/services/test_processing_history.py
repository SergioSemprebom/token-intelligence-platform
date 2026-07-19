"""Testes do serviço de histórico (app/services/processing_history.py)."""

from __future__ import annotations

import hashlib
import logging
from decimal import Decimal

import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.splitter import dividir_texto_por_tokens
from app.core.tokenizer import analisar_texto
from app.database.models.processamento import (
    TIPO_OPERACAO_ANALISE,
    TIPO_OPERACAO_COMPARACAO,
    TIPO_OPERACAO_DIVISAO,
    TIPO_OPERACAO_ESTIMATIVA_CUSTO,
    Processamento,
)
from app.repositories.processamento_repository import ProcessamentoRepository
from app.services.cost_estimator import estimar_custo_por_modelo
from app.services.model_comparator import comparar_modelos
from app.services.processing_history import (
    calcular_hash_texto,
    calcular_preview_texto,
    registrar_analise,
    registrar_comparacao,
    registrar_divisao,
    registrar_erro,
    registrar_estimativa_custo,
)


def test_calcular_hash_texto_eh_sha256_do_texto_normalizado() -> None:
    esperado = hashlib.sha256("Ola mundo".encode("utf-8")).hexdigest()

    assert calcular_hash_texto("  Ola mundo  ") == esperado


def test_calcular_preview_texto_limita_a_200_caracteres() -> None:
    texto = "a" * 300

    preview = calcular_preview_texto(texto)

    assert len(preview) == 200
    assert preview == "a" * 200


def test_processamento_nao_possui_coluna_de_token_ids() -> None:
    assert "token_ids" not in Processamento.__table__.columns


def test_registrar_analise_persiste_campos_esperados(sessao_bd: Session) -> None:
    texto = "Texto de teste para análise"
    resultado = analisar_texto(texto=texto, modelo="gpt-4o")

    registro = registrar_analise(
        sessao=sessao_bd, texto=texto, resultado=resultado, fallback_utilizado=False
    )

    assert registro is not None
    assert registro.tipo_operacao == TIPO_OPERACAO_ANALISE
    assert registro.tokens_entrada == resultado["tokens"]
    assert registro.total_tokens == resultado["tokens"]
    assert registro.texto_hash == calcular_hash_texto(texto)
    assert registro.texto_preview == texto
    assert registro.sucesso is True


def test_registrar_divisao_persiste_metadados_dos_blocos(sessao_bd: Session) -> None:
    texto = "palavra " * 200
    blocos = dividir_texto_por_tokens(
        texto=texto, modelo="gpt-4o", limite_tokens=50, sobreposicao=5
    )
    total_tokens_original = blocos[-1].token_final + 1

    registro = registrar_divisao(
        sessao=sessao_bd,
        texto=texto,
        modelo="gpt-4o",
        limite_tokens=50,
        sobreposicao_tokens=5,
        total_blocos=len(blocos),
        total_tokens_original=total_tokens_original,
    )

    assert registro is not None
    assert registro.tipo_operacao == TIPO_OPERACAO_DIVISAO
    assert registro.quantidade_blocos == len(blocos)
    assert registro.limite_tokens_bloco == 50
    assert registro.sobreposicao_tokens == 5
    assert registro.total_tokens == total_tokens_original


def test_registrar_comparacao_cria_um_registro_por_modelo(sessao_bd: Session) -> None:
    texto = "Texto para comparar"
    resultados = comparar_modelos(texto=texto, modelos=["gpt-4o", "gpt-3.5-turbo"])

    registros = registrar_comparacao(sessao=sessao_bd, texto=texto, resultados=resultados)

    assert len(registros) == 2
    assert {registro.tipo_operacao for registro in registros} == {TIPO_OPERACAO_COMPARACAO}
    assert {registro.modelo_solicitado for registro in registros} == {
        "gpt-4o",
        "gpt-3.5-turbo",
    }


def test_registrar_estimativa_custo_mantem_precisao_decimal(sessao_bd: Session) -> None:
    resultado = estimar_custo_por_modelo(tokens_entrada=1000, tokens_saida=500, modelo="gpt-4o")

    registro = registrar_estimativa_custo(
        sessao=sessao_bd,
        modelo=resultado.modelo,
        tokens_entrada=resultado.tokens_entrada,
        tokens_saida=resultado.tokens_saida,
        custo_entrada=resultado.custo_entrada,
        custo_saida=resultado.custo_saida,
        custo_total=resultado.custo_total,
        moeda="USD",
    )

    assert registro is not None
    assert registro.tipo_operacao == TIPO_OPERACAO_ESTIMATIVA_CUSTO
    assert isinstance(registro.custo_total, Decimal)
    assert registro.custo_total == resultado.custo_total
    assert registro.moeda == "USD"


def test_registrar_erro_persiste_sucesso_falso_e_mensagem(sessao_bd: Session) -> None:
    registro = registrar_erro(
        sessao=sessao_bd,
        tipo_operacao=TIPO_OPERACAO_ANALISE,
        mensagem_erro="Modelo inválido informado pelo cliente.",
        modelo_solicitado="modelo-invalido",
        texto="texto de exemplo",
    )

    assert registro is not None
    assert registro.sucesso is False
    assert registro.mensagem_erro == "Modelo inválido informado pelo cliente."
    assert registro.texto_hash == calcular_hash_texto("texto de exemplo")


def test_falha_de_persistencia_nao_interrompe_operacao_principal(
    sessao_bd: Session,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Simula indisponibilidade do banco: o histórico falha, mas nada é levantado."""

    def _criar_com_falha(self: ProcessamentoRepository, processamento: Processamento) -> None:
        raise SQLAlchemyError("falha simulada de conexão com o banco")

    monkeypatch.setattr(ProcessamentoRepository, "criar", _criar_com_falha)

    texto = "Texto que deveria continuar sendo processado normalmente"
    resultado = analisar_texto(texto=texto, modelo="gpt-4o")

    with caplog.at_level(logging.ERROR):
        registro = registrar_analise(
            sessao=sessao_bd, texto=texto, resultado=resultado, fallback_utilizado=False
        )

    assert registro is None
    assert any("histórico" in mensagem.lower() for mensagem in caplog.messages)
    assert not any("DATABASE_URL" in mensagem for mensagem in caplog.messages)
