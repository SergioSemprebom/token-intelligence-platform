"""Fábrica de engine e sessões do SQLAlchemy."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config.settings import obter_configuracoes


def criar_engine(database_url: str | None = None) -> Engine:
    """Cria a engine do SQLAlchemy a partir da URL configurada.

    A criação da engine não abre conexão imediatamente, portanto a
    aplicação pode ser importada mesmo sem um PostgreSQL disponível.
    """
    configuracoes = obter_configuracoes()
    return create_engine(
        database_url or configuracoes.database_url,
        echo=configuracoes.database_echo,
        pool_pre_ping=True,
    )


engine = criar_engine()

FabricaDeSessao = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def obter_sessao() -> Generator[Session, None, None]:
    """Fornece uma sessão do SQLAlchemy, garantindo o fechamento ao final."""
    sessao = FabricaDeSessao()
    try:
        yield sessao
    finally:
        sessao.close()
