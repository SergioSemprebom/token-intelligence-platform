"""Executa a carga incremental da camada analítica (schema `analytics`).

Uso:

    uv run python scripts/refresh_analytics.py

Nunca imprime a DATABASE_URL completa (usuário/senha) nem detalhes internos
de erros de banco — apenas host, porta e nome do banco, além do tipo do erro.
"""

from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy.exc import OperationalError, SQLAlchemyError  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.config.settings import obter_configuracoes  # noqa: E402
from app.database.session import criar_engine  # noqa: E402
from app.repositories.analytics_repository import AnalyticsRepository  # noqa: E402


def _descrever_servidor_sem_credenciais(database_url: str) -> str:
    """Retorna apenas host:porta/banco, nunca usuário ou senha."""
    partes = urlsplit(database_url)
    host = partes.hostname or "desconhecido"
    porta = partes.port or "padrão"
    banco = partes.path.lstrip("/") or "desconhecido"
    return f"{host}:{porta}/{banco}"


def main() -> int:
    configuracoes = obter_configuracoes()
    servidor = _descrever_servidor_sem_credenciais(configuracoes.database_url)
    print(f"Conectando à camada analítica em {servidor}...")

    engine = criar_engine(configuracoes.database_url)
    fabrica_sessao = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    sessao = fabrica_sessao()

    repositorio = AnalyticsRepository(sessao)

    try:
        resultado = repositorio.executar_refresh()
    except OperationalError:
        print(
            "Erro: não foi possível conectar ao PostgreSQL. Verifique se o banco "
            "está no ar e se DATABASE_URL está configurada corretamente (.env).",
            file=sys.stderr,
        )
        return 1
    except SQLAlchemyError as erro:
        print(
            f"Erro ao executar analytics.refresh_modelo_analitico() ({type(erro).__name__}). "
            "Verifique se 'uv run alembic upgrade head' já foi executado.",
            file=sys.stderr,
        )
        return 1

    print("Refresh da camada analítica concluído com sucesso.")
    print(f"  Modelos novos inseridos em d_modelo   : {resultado.dimensoes_modelo_inseridas}")
    print(f"  Fatos inseridos em f_processamentos   : {resultado.fatos_inseridos}")
    print(f"  Fatos atualizados em f_processamentos : {resultado.fatos_atualizados}")
    print(f"  Executado em                          : {resultado.executado_em}")

    try:
        resultado_compactacoes = repositorio.executar_refresh_compactacoes()
    except SQLAlchemyError as erro:
        print(
            f"\nAviso: falha ao executar analytics.refresh_compactacoes_prompt() "
            f"({type(erro).__name__}). Verifique se 'uv run alembic upgrade head' "
            "já foi executado (migração da Fase 7).",
            file=sys.stderr,
        )
        return 1
    finally:
        sessao.close()
        engine.dispose()

    print("\nRefresh da fato de compactações de prompt concluído com sucesso.")
    print(f"  Modelos novos inseridos em d_modelo         : {resultado_compactacoes.dimensoes_modelo_inseridas}")
    print(f"  Fatos inseridos em f_compactacoes_prompt    : {resultado_compactacoes.fatos_inseridos}")
    print(f"  Fatos atualizados em f_compactacoes_prompt  : {resultado_compactacoes.fatos_atualizados}")
    print(f"  Executado em                                : {resultado_compactacoes.executado_em}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
