"""Testes unitários do script scripts/refresh_analytics.py.

Cobrem apenas a função pura de formatação do servidor (sem usuário/senha) —
o restante do script depende de um PostgreSQL real e é validado manualmente
via `uv run python scripts/refresh_analytics.py` (ver README.md e CLAUDE.md).
"""

from __future__ import annotations

from scripts.refresh_analytics import _descrever_servidor_sem_credenciais


def test_descreve_servidor_sem_expor_usuario_e_senha() -> None:
    url = "postgresql+psycopg://usuario_secreto:senha_secreta@localhost:5434/token_intelligence"

    resultado = _descrever_servidor_sem_credenciais(url)

    assert resultado == "localhost:5434/token_intelligence"
    assert "usuario_secreto" not in resultado
    assert "senha_secreta" not in resultado


def test_descreve_servidor_com_porta_padrao_quando_ausente() -> None:
    url = "postgresql+psycopg://usuario:senha@localhost/token_intelligence"

    resultado = _descrever_servidor_sem_credenciais(url)

    assert resultado == "localhost:padrão/token_intelligence"
    assert "usuario" not in resultado
    assert "senha" not in resultado
