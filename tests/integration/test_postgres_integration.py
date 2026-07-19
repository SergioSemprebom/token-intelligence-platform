"""Testes de integração que exigem um PostgreSQL real e acessível.

São ignorados automaticamente (skip) quando `DATABASE_URL` não aponta para
um banco alcançável — os testes unitários do restante da suíte nunca
dependem de PostgreSQL. Para forçar apenas estes testes:

    uv run pytest -m integration -v
"""

from __future__ import annotations

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError

from app.config.settings import obter_configuracoes
from app.database.session import criar_engine


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
            "PostgreSQL real não está acessível via DATABASE_URL. "
            "Configure .env com um banco válido e execute `uv run alembic upgrade head` "
            "antes de rodar estes testes."
        ),
    ),
]


def test_conexao_com_postgresql_real() -> None:
    engine = criar_engine(obter_configuracoes().database_url)
    with engine.connect() as conexao:
        resultado = conexao.execute(text("SELECT 1")).scalar_one()

    assert resultado == 1


def test_tabela_processamentos_existe_apos_migracao() -> None:
    engine = criar_engine(obter_configuracoes().database_url)
    inspetor = inspect(engine)

    assert "processamentos" in inspetor.get_table_names()
