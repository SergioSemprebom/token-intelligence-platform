"""Testes das configurações carregadas via pydantic-settings."""

from __future__ import annotations

import pytest

from app.config.settings import Settings


def test_salvar_texto_completo_eh_falso_por_padrao() -> None:
    configuracoes = Settings(_env_file=None)

    assert configuracoes.salvar_texto_completo is False


def test_database_echo_eh_falso_por_padrao() -> None:
    configuracoes = Settings(_env_file=None)

    assert configuracoes.database_echo is False


def test_database_url_aceita_sobrescrita_por_variavel_de_ambiente(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://usuario:senha@host:5432/outro_banco")

    configuracoes = Settings(_env_file=None)

    assert configuracoes.database_url == (
        "postgresql+psycopg://usuario:senha@host:5432/outro_banco"
    )
