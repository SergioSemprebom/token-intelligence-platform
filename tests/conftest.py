"""Configuração compartilhada dos testes automatizados.

Os testes unitários nunca dependem de um PostgreSQL real: usam SQLite em
memória, criado via `Base.metadata.create_all` (justificado aqui porque não
há Alembic disponível dentro do banco efêmero de cada teste). A coluna
`metadados` usa um tipo JSON genérico que faz fallback para JSON simples no
SQLite (ver app/database/models/processamento.py) — uma diferença real entre
os dialetos, não escondida, apenas tornada compatível com os dois bancos.
"""

from __future__ import annotations

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.app import app
from app.api.dependencies import obter_sessao_bd
from app.database.base import Base
from app.database.models import Processamento  # noqa: F401 — registra a tabela no metadata


@pytest.fixture()
def sessao_bd() -> Generator[Session, None, None]:
    """Fornece uma sessão SQLite em memória, isolada por teste."""
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    fabrica = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    sessao = fabrica()
    try:
        yield sessao
    finally:
        sessao.close()
        engine.dispose()


@pytest.fixture(autouse=True)
def _sobrescrever_sessao_bd_na_api(sessao_bd: Session) -> Generator[None, None, None]:
    """Garante que as rotas da API usem o SQLite de teste, nunca o PostgreSQL real."""

    def _fornecer_sessao_teste() -> Generator[Session, None, None]:
        yield sessao_bd

    app.dependency_overrides[obter_sessao_bd] = _fornecer_sessao_teste
    yield
    app.dependency_overrides.pop(obter_sessao_bd, None)
