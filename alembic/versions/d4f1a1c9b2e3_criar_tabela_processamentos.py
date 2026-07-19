"""criar tabela processamentos

Revision ID: d4f1a1c9b2e3
Revises:
Create Date: 2026-07-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = "d4f1a1c9b2e3"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "processamentos",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            index=True,
        ),
        sa.Column("tipo_operacao", sa.String(length=50), nullable=False, index=True),
        sa.Column("origem", sa.String(length=20), nullable=False, index=True),
        sa.Column(
            "modelo_solicitado", sa.String(length=100), nullable=True, index=True
        ),
        sa.Column("encoding_utilizado", sa.String(length=100), nullable=True),
        sa.Column("fallback_utilizado", sa.Boolean(), nullable=False),
        sa.Column("caracteres", sa.Integer(), nullable=True),
        sa.Column("palavras", sa.Integer(), nullable=True),
        sa.Column("bytes_utf8", sa.Integer(), nullable=True),
        sa.Column("tokens_entrada", sa.Integer(), nullable=False),
        sa.Column("tokens_saida", sa.Integer(), nullable=False),
        sa.Column("total_tokens", sa.Integer(), nullable=False),
        sa.Column("quantidade_blocos", sa.Integer(), nullable=True),
        sa.Column("limite_tokens_bloco", sa.Integer(), nullable=True),
        sa.Column("sobreposicao_tokens", sa.Integer(), nullable=True),
        sa.Column("custo_entrada", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("custo_saida", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("custo_total", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("moeda", sa.String(length=10), nullable=True),
        sa.Column(
            "tempo_processamento_ms", sa.Numeric(precision=18, scale=4), nullable=True
        ),
        sa.Column("texto_hash", sa.String(length=64), nullable=True, index=True),
        sa.Column("texto_preview", sa.String(length=200), nullable=True),
        sa.Column("sucesso", sa.Boolean(), nullable=False, index=True),
        sa.Column("mensagem_erro", sa.Text(), nullable=True),
        sa.Column("metadados", JSONB(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("processamentos")
