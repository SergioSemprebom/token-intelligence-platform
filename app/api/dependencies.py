"""Dependências compartilhadas entre as rotas da API."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

from sqlalchemy.orm import Session

from app.database.session import obter_sessao
from app.services.cost_estimator import CAMINHO_PRECOS_PADRAO


def obter_caminho_precos() -> Path:
    """Fornece o caminho do arquivo de preços de modelos.

    Isolar isso como dependência permite substituir o arquivo de preços em
    testes automatizados via `app.dependency_overrides`, sem alterar
    app/services/cost_estimator.py.
    """
    return CAMINHO_PRECOS_PADRAO


def obter_sessao_bd() -> Generator[Session, None, None]:
    """Fornece uma sessão de banco de dados às rotas.

    Isolar isso como dependência permite substituir a sessão em testes
    automatizados via `app.dependency_overrides`, sem depender de um
    PostgreSQL real.
    """
    yield from obter_sessao()
