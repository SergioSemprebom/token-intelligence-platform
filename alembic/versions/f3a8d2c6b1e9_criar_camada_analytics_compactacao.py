"""criar camada analytics de compactacoes_prompt

Estende o schema `analytics` (Fase 6) com suporte à Fase 7: a dimensão
`d_nivel_compactacao`, a fato `f_compactacoes_prompt`, as views
`vw_powerbi_compactacoes*` e a função `analytics.refresh_compactacoes_prompt()`
— uma função separada de `analytics.refresh_modelo_analitico()`, para não
alterar sua assinatura nem o comportamento já existente.

O DDL completo vive em analytics/sql/08..11 (fonte única de verdade); esta
migração apenas lê e executa esses arquivos. O downgrade remove somente os
objetos criados aqui (função, views, fato e dimensão), nunca o restante do
schema `analytics` nem `public.processamentos`/`public.compactacoes_prompt`.

Revision ID: f3a8d2c6b1e9
Revises: e7f1c9a2b4d6
Create Date: 2026-07-19 00:00:00.000000

"""
from pathlib import Path
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f3a8d2c6b1e9"
down_revision: Union[str, Sequence[str], None] = "e7f1c9a2b4d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_DIRETORIO_SQL = Path(__file__).resolve().parents[2] / "analytics" / "sql"

_ARQUIVOS_UPGRADE = (
    "08_create_compression_dimension.sql",
    "09_create_compression_fact.sql",
    "10_create_compression_views.sql",
    "11_create_compression_refresh.sql",
)


def _executar_arquivo_sql(nome_arquivo: str) -> None:
    caminho = _DIRETORIO_SQL / nome_arquivo
    op.execute(caminho.read_text(encoding="utf-8"))


def upgrade() -> None:
    """Upgrade schema."""
    for nome_arquivo in _ARQUIVOS_UPGRADE:
        _executar_arquivo_sql(nome_arquivo)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP FUNCTION IF EXISTS analytics.refresh_compactacoes_prompt()")
    op.execute("DROP VIEW IF EXISTS analytics.vw_powerbi_resumo_compactacao_mensal")
    op.execute("DROP VIEW IF EXISTS analytics.vw_powerbi_resumo_compactacao_diario")
    op.execute("DROP VIEW IF EXISTS analytics.vw_powerbi_compactacoes")
    op.execute("DROP TABLE IF EXISTS analytics.f_compactacoes_prompt")
    op.execute("DROP TABLE IF EXISTS analytics.d_nivel_compactacao")
