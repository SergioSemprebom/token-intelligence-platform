"""criar tabela compactacoes_prompt

Cria a tabela `compactacoes_prompt` (Fase 7 — auditor/compactador local de
prompts), com FK opcional para `processamentos.id`. Nunca guarda o texto
completo nem `token_ids`: apenas hash (SHA-256) e preview de 200 caracteres
do texto original e do texto compactado.

Revision ID: e7f1c9a2b4d6
Revises: d93bc6ab6522
Create Date: 2026-07-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = "e7f1c9a2b4d6"
down_revision: Union[str, Sequence[str], None] = "d93bc6ab6522"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "compactacoes_prompt",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "processamento_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("processamentos.id"),
            nullable=True,
        ),
        sa.Column("origem", sa.String(length=20), nullable=False, index=True),
        sa.Column("modelo_solicitado", sa.String(length=100), nullable=True, index=True),
        sa.Column("encoding_utilizado", sa.String(length=100), nullable=True),
        sa.Column("nivel_compactacao", sa.String(length=20), nullable=False, index=True),
        sa.Column("tokens_originais", sa.Integer(), nullable=False),
        sa.Column("tokens_compactados", sa.Integer(), nullable=False),
        sa.Column("tokens_economizados", sa.Integer(), nullable=False),
        sa.Column("reducao_percentual", sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column("caracteres_originais", sa.Integer(), nullable=True),
        sa.Column("caracteres_compactados", sa.Integer(), nullable=True),
        sa.Column("texto_original_hash", sa.String(length=64), nullable=True, index=True),
        sa.Column("texto_compactado_hash", sa.String(length=64), nullable=True),
        sa.Column("preview_original", sa.String(length=200), nullable=True),
        sa.Column("preview_compactado", sa.String(length=200), nullable=True),
        sa.Column("quantidade_alteracoes", sa.Integer(), nullable=False),
        sa.Column("risco", sa.String(length=20), nullable=False),
        sa.Column("aprovado", sa.Boolean(), nullable=False, index=True),
        sa.Column("aprovado_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("compactacao_aplicada", sa.Boolean(), nullable=False),
        sa.Column("fallback_utilizado", sa.Boolean(), nullable=False),
        sa.Column("avisos", JSONB(), nullable=True),
        sa.Column("alteracoes", JSONB(), nullable=True),
        sa.Column("sucesso", sa.Boolean(), nullable=False, index=True),
        sa.Column("mensagem_erro", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("compactacoes_prompt")
