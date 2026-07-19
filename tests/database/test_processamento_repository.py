"""Testes do ProcessamentoRepository, sem depender de PostgreSQL real."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.database.models.processamento import (
    ORIGEM_API,
    TIPO_OPERACAO_ANALISE,
    TIPO_OPERACAO_DIVISAO,
    Processamento,
)
from app.repositories.processamento_repository import ProcessamentoRepository

AGORA = datetime(2026, 7, 18, 12, 0, 0, tzinfo=timezone.utc)


def _criar_processamento(
    tipo_operacao: str = TIPO_OPERACAO_ANALISE,
    modelo_solicitado: str | None = "gpt-4o",
    sucesso: bool = True,
    criado_em: datetime | None = None,
    tokens_entrada: int = 10,
    tokens_saida: int = 0,
    custo_total: Decimal | None = None,
) -> Processamento:
    return Processamento(
        tipo_operacao=tipo_operacao,
        origem=ORIGEM_API,
        modelo_solicitado=modelo_solicitado,
        fallback_utilizado=False,
        tokens_entrada=tokens_entrada,
        tokens_saida=tokens_saida,
        total_tokens=tokens_entrada + tokens_saida,
        custo_total=custo_total,
        sucesso=sucesso,
        criado_em=criado_em or AGORA,
    )


def test_criar_processamento_persiste_e_gera_id(sessao_bd: Session) -> None:
    repositorio = ProcessamentoRepository(sessao_bd)

    criado = repositorio.criar(_criar_processamento())

    assert isinstance(criado.id, uuid.UUID)
    assert criado.criado_em is not None


def test_buscar_por_id_existente(sessao_bd: Session) -> None:
    repositorio = ProcessamentoRepository(sessao_bd)
    criado = repositorio.criar(_criar_processamento())

    encontrado = repositorio.buscar_por_id(criado.id)

    assert encontrado is not None
    assert encontrado.id == criado.id


def test_buscar_por_id_inexistente_retorna_none(sessao_bd: Session) -> None:
    repositorio = ProcessamentoRepository(sessao_bd)

    assert repositorio.buscar_por_id(uuid.uuid4()) is None


def test_listar_ordena_por_criado_em_decrescente(sessao_bd: Session) -> None:
    repositorio = ProcessamentoRepository(sessao_bd)
    mais_antigo = repositorio.criar(_criar_processamento(criado_em=AGORA - timedelta(minutes=5)))
    mais_recente = repositorio.criar(_criar_processamento(criado_em=AGORA))

    resultados = repositorio.listar()

    assert [item.id for item in resultados] == [mais_recente.id, mais_antigo.id]


def test_listar_filtra_por_tipo_operacao(sessao_bd: Session) -> None:
    repositorio = ProcessamentoRepository(sessao_bd)
    repositorio.criar(_criar_processamento(tipo_operacao=TIPO_OPERACAO_ANALISE))
    repositorio.criar(_criar_processamento(tipo_operacao=TIPO_OPERACAO_DIVISAO))

    resultados = repositorio.listar(tipo_operacao=TIPO_OPERACAO_DIVISAO)

    assert len(resultados) == 1
    assert resultados[0].tipo_operacao == TIPO_OPERACAO_DIVISAO


def test_listar_respeita_limite_e_offset(sessao_bd: Session) -> None:
    repositorio = ProcessamentoRepository(sessao_bd)
    for indice in range(5):
        repositorio.criar(_criar_processamento(criado_em=AGORA - timedelta(minutes=indice)))

    pagina = repositorio.listar(limite=2, offset=2)

    assert len(pagina) == 2


def test_contar_respeita_filtros(sessao_bd: Session) -> None:
    repositorio = ProcessamentoRepository(sessao_bd)
    repositorio.criar(_criar_processamento(sucesso=True))
    repositorio.criar(_criar_processamento(sucesso=False))

    assert repositorio.contar() == 2
    assert repositorio.contar(sucesso=True) == 1
    assert repositorio.contar(sucesso=False) == 1


def test_listar_por_tipo(sessao_bd: Session) -> None:
    repositorio = ProcessamentoRepository(sessao_bd)
    repositorio.criar(_criar_processamento(tipo_operacao=TIPO_OPERACAO_ANALISE))
    repositorio.criar(_criar_processamento(tipo_operacao=TIPO_OPERACAO_DIVISAO))

    resultados = repositorio.listar_por_tipo(TIPO_OPERACAO_ANALISE)

    assert len(resultados) == 1
    assert resultados[0].tipo_operacao == TIPO_OPERACAO_ANALISE


def test_listar_por_periodo(sessao_bd: Session) -> None:
    repositorio = ProcessamentoRepository(sessao_bd)
    repositorio.criar(_criar_processamento(criado_em=AGORA - timedelta(days=10)))
    dentro_do_periodo = repositorio.criar(_criar_processamento(criado_em=AGORA))

    resultados = repositorio.listar_por_periodo(
        data_inicio=AGORA - timedelta(days=1), data_fim=AGORA + timedelta(days=1)
    )

    assert len(resultados) == 1
    assert resultados[0].id == dentro_do_periodo.id


def test_obter_resumo_agrega_metricas(sessao_bd: Session) -> None:
    repositorio = ProcessamentoRepository(sessao_bd)
    repositorio.criar(
        _criar_processamento(
            tipo_operacao=TIPO_OPERACAO_ANALISE,
            modelo_solicitado="gpt-4o",
            tokens_entrada=100,
            custo_total=Decimal("1.50"),
            sucesso=True,
        )
    )
    repositorio.criar(
        _criar_processamento(
            tipo_operacao=TIPO_OPERACAO_DIVISAO,
            modelo_solicitado="gpt-4o",
            tokens_entrada=50,
            custo_total=Decimal("0.50"),
            sucesso=False,
        )
    )

    resumo = repositorio.obter_resumo()

    assert resumo.total_processamentos == 2
    assert resumo.total_tokens_entrada == 150
    assert resumo.custo_total == Decimal("2.00")
    assert resumo.quantidade_sucessos == 1
    assert resumo.quantidade_erros == 1
    assert resumo.processamentos_por_tipo[TIPO_OPERACAO_ANALISE] == 1
    assert resumo.processamentos_por_tipo[TIPO_OPERACAO_DIVISAO] == 1
    assert resumo.processamentos_por_modelo["gpt-4o"] == 2
