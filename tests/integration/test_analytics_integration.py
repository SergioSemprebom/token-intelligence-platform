"""Testes de integração da camada analítica (schema `analytics`).

Exigem um PostgreSQL real, acessível via DATABASE_URL, com as migrações já
aplicadas (`uv run alembic upgrade head`) — inclusive a migração que cria o
schema `analytics`. São ignorados automaticamente (skip) quando o banco não
está acessível, no mesmo padrão de tests/integration/test_postgres_integration.py.

Para forçar apenas estes testes:

    uv run pytest tests/integration/test_analytics_integration.py -v
"""

from __future__ import annotations

import uuid
from datetime import datetime

import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

from app.config.settings import obter_configuracoes
from app.database.models.processamento import ORIGEM_API, TIPO_OPERACAO_ANALISE, Processamento
from app.database.session import criar_engine
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.processamento_repository import ProcessamentoRepository


def _postgres_disponivel() -> bool:
    try:
        engine = criar_engine(obter_configuracoes().database_url)
        with engine.connect() as conexao:
            conexao.execute(text("SELECT 1"))
        return True
    except OperationalError:
        return False
    finally:
        try:
            engine.dispose()
        except NameError:
            pass


pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not _postgres_disponivel(),
        reason=(
            "PostgreSQL real não está acessível via DATABASE_URL. Configure .env "
            "e execute `uv run alembic upgrade head` (inclui a camada analytics) "
            "antes de rodar estes testes."
        ),
    ),
]


@pytest.fixture()
def sessao_postgres() -> Session:
    engine = criar_engine(obter_configuracoes().database_url)
    fabrica = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    sessao = fabrica()
    try:
        yield sessao
    finally:
        sessao.close()
        engine.dispose()


def _criar_processamento_unico(sessao: Session) -> Processamento:
    modelo_unico = f"modelo-teste-{uuid.uuid4().hex[:8]}"
    return ProcessamentoRepository(sessao).criar(
        Processamento(
            tipo_operacao=TIPO_OPERACAO_ANALISE,
            origem=ORIGEM_API,
            modelo_solicitado=modelo_unico,
            fallback_utilizado=False,
            tokens_entrada=42,
            tokens_saida=0,
            total_tokens=42,
            sucesso=True,
        )
    )


def test_calendario_populado_de_2024_a_2035(sessao_postgres: Session) -> None:
    total = sessao_postgres.execute(text("SELECT COUNT(*) FROM analytics.d_calendario")).scalar_one()

    assert total == (datetime(2036, 1, 1) - datetime(2024, 1, 1)).days


def test_calendario_calcula_data_id_no_formato_yyyymmdd(sessao_postgres: Session) -> None:
    linha = sessao_postgres.execute(
        text(
            "SELECT data_id, ano, numero_mes, nome_mes FROM analytics.d_calendario "
            "WHERE data = :data"
        ),
        {"data": "2024-01-01"},
    ).one()

    assert linha.data_id == 20240101
    assert linha.ano == 2024
    assert linha.numero_mes == 1
    assert linha.nome_mes == "Janeiro"


def test_calendario_ordena_corretamente_por_ano_mes(sessao_postgres: Session) -> None:
    valores = list(
        sessao_postgres.execute(
            text(
                "SELECT DISTINCT ano_mes_numero FROM analytics.d_calendario "
                "WHERE ano = 2024 ORDER BY ano_mes_numero"
            )
        ).scalars()
    )

    assert valores == sorted(valores)
    assert valores[0] == 202401
    assert valores[-1] == 202412


def test_dimensoes_possuem_chave_especial_nao_informado(sessao_postgres: Session) -> None:
    assert (
        sessao_postgres.execute(
            text("SELECT modelo_nome FROM analytics.d_modelo WHERE modelo_id = 0")
        ).scalar_one()
        == "Não informado"
    )
    assert (
        sessao_postgres.execute(
            text("SELECT operacao_codigo FROM analytics.d_operacao WHERE operacao_id = 0")
        ).scalar_one()
        == "nao_informado"
    )
    assert (
        sessao_postgres.execute(
            text("SELECT origem_codigo FROM analytics.d_origem WHERE origem_id = 0")
        ).scalar_one()
        == "nao_informado"
    )
    assert (
        sessao_postgres.execute(
            text("SELECT status_codigo FROM analytics.d_status WHERE status_id = 0")
        ).scalar_one()
        == "nao_informado"
    )


def test_d_operacao_mapeia_operacoes_conhecidas(sessao_postgres: Session) -> None:
    codigos = set(
        sessao_postgres.execute(text("SELECT operacao_codigo FROM analytics.d_operacao")).scalars()
    )

    assert {"analise", "divisao", "comparacao", "estimativa_custo", "nao_informado"} <= codigos


def test_views_powerbi_existem(sessao_postgres: Session) -> None:
    views = set(
        sessao_postgres.execute(
            text(
                "SELECT table_name FROM information_schema.views WHERE table_schema = 'analytics'"
            )
        ).scalars()
    )

    assert {
        "vw_powerbi_processamentos",
        "vw_powerbi_resumo_diario",
        "vw_powerbi_resumo_mensal",
        "vw_powerbi_textos_repetidos",
    } <= views


def test_fato_nao_possui_texto_completo_nem_metadados(sessao_postgres: Session) -> None:
    colunas = set(
        sessao_postgres.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema = 'analytics' AND table_name = 'f_processamentos'"
            )
        ).scalars()
    )

    assert "texto_preview" not in colunas
    assert "metadados" not in colunas
    assert "token_ids" not in colunas


def test_refresh_sem_registros_novos_funciona_sem_erro(sessao_postgres: Session) -> None:
    repositorio = AnalyticsRepository(sessao_postgres)

    repositorio.executar_refresh()
    resultado = repositorio.executar_refresh()

    assert resultado.fatos_inseridos == 0
    assert resultado.dimensoes_modelo_inseridas == 0


def test_refresh_insere_fato_para_processamento_novo(sessao_postgres: Session) -> None:
    processamento = _criar_processamento_unico(sessao_postgres)

    resultado = AnalyticsRepository(sessao_postgres).executar_refresh()

    assert resultado.dimensoes_modelo_inseridas >= 1
    assert resultado.fatos_inseridos >= 1

    linha_fato = sessao_postgres.execute(
        text(
            "SELECT f.tokens_entrada, m.modelo_nome FROM analytics.f_processamentos f "
            "JOIN analytics.d_modelo m ON m.modelo_id = f.modelo_id "
            "WHERE f.processamento_id = :id"
        ),
        {"id": str(processamento.id)},
    ).one()

    assert linha_fato.tokens_entrada == 42
    assert linha_fato.modelo_nome == processamento.modelo_solicitado


def test_refresh_nao_duplica_processamento_id(sessao_postgres: Session) -> None:
    processamento = _criar_processamento_unico(sessao_postgres)

    AnalyticsRepository(sessao_postgres).executar_refresh()
    AnalyticsRepository(sessao_postgres).executar_refresh()

    quantidade = sessao_postgres.execute(
        text("SELECT COUNT(*) FROM analytics.f_processamentos WHERE processamento_id = :id"),
        {"id": str(processamento.id)},
    ).scalar_one()

    assert quantidade == 1


def test_controle_carga_registra_execucao(sessao_postgres: Session) -> None:
    AnalyticsRepository(sessao_postgres).executar_refresh()

    status = AnalyticsRepository(sessao_postgres).obter_ultima_carga()

    assert status is not None
    assert status.processo == "refresh_modelo_analitico"
    assert status.status == "sucesso"
    assert status.finalizado_em is not None
