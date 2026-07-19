"""criar camada analytics

Cria o schema `analytics` (modelo estrela para o Power BI): dimensões
(d_calendario, d_modelo, d_operacao, d_origem, d_status), a fato
f_processamentos, a tabela de controle de carga, a função de refresh
incremental e as views vw_powerbi_*.

O DDL completo vive em analytics/sql/01..05 (fonte única de verdade); esta
migração apenas lê e executa esses arquivos, para não duplicar SQL entre o
repositório de scripts e a migração.

O downgrade remove somente o schema `analytics` (CASCADE sobre seus próprios
objetos). A tabela operacional `processamentos` nunca é tocada.

Revision ID: d93bc6ab6522
Revises: d4f1a1c9b2e3
Create Date: 2026-07-18 23:13:05.422712

"""
from pathlib import Path
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd93bc6ab6522'
down_revision: Union[str, Sequence[str], None] = 'd4f1a1c9b2e3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_DIRETORIO_SQL = Path(__file__).resolve().parents[2] / "analytics" / "sql"

_ARQUIVOS_UPGRADE = (
    "01_create_schema.sql",
    "02_create_dimensions.sql",
    "03_create_fact.sql",
    "04_create_views.sql",
    "05_create_refresh_functions.sql",
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
    op.execute("DROP SCHEMA IF EXISTS analytics CASCADE")
