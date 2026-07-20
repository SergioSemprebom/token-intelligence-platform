"""criar tabela provider_connections

Revision ID: a8b1c2d3e4f5
Revises: f3a8d2c6b1e9
Create Date: 2026-07-20
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a8b1c2d3e4f5"
down_revision: Union[str, Sequence[str], None] = "f3a8d2c6b1e9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "provider_connections",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("provider_slug", sa.String(length=50), nullable=False),
        sa.Column("nome", sa.String(length=80), nullable=False),
        sa.Column("encrypted_api_key", sa.Text(), nullable=False),
        sa.Column("credential_hint", sa.String(length=40), nullable=False),
        sa.Column("orcamento_mensal", sa.Numeric(18, 2), nullable=False),
        sa.Column("moeda", sa.String(length=3), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("ultima_sincronizacao_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ultimo_status", sa.String(length=40), nullable=False),
        sa.Column("ultimo_erro", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_provider_connections_provider_slug", "provider_connections", ["provider_slug"])
    op.create_index("ix_provider_connections_ativo", "provider_connections", ["ativo"])


def downgrade() -> None:
    op.drop_index("ix_provider_connections_ativo", table_name="provider_connections")
    op.drop_index("ix_provider_connections_provider_slug", table_name="provider_connections")
    op.drop_table("provider_connections")
