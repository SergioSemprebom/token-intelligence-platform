"""Modelo da tabela `compactacoes_prompt`, resultados do compactador de prompts.

Assim como `processamentos`, esta tabela nunca guarda o texto completo nem
`token_ids` — apenas hash (SHA-256) e um preview de 200 caracteres do texto
original e do texto compactado.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.database.base import Base

NIVEL_CONSERVADOR = "conservador"
NIVEL_MODERADO = "moderado"
NIVEL_AGRESSIVO = "agressivo"

NIVEIS_COMPACTACAO_VALIDOS = {NIVEL_CONSERVADOR, NIVEL_MODERADO, NIVEL_AGRESSIVO}

# JSON genérico que se torna JSONB no PostgreSQL, com fallback para JSON
# simples no SQLite dos testes unitários (mesmo padrão de processamento.py).
_TipoListaJson = JSON().with_variant(JSONB, "postgresql")


class CompactacaoPrompt(Base):
    """Registro de uma compactação de prompt gerada localmente (regras)."""

    __tablename__ = "compactacoes_prompt"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    processamento_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("processamentos.id"), nullable=True
    )

    origem: Mapped[str] = mapped_column(String(20), index=True)
    modelo_solicitado: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    encoding_utilizado: Mapped[str | None] = mapped_column(String(100), nullable=True)
    nivel_compactacao: Mapped[str] = mapped_column(String(20), index=True)

    tokens_originais: Mapped[int] = mapped_column(default=0)
    tokens_compactados: Mapped[int] = mapped_column(default=0)
    tokens_economizados: Mapped[int] = mapped_column(default=0)
    reducao_percentual: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=Decimal("0"))

    caracteres_originais: Mapped[int | None] = mapped_column(nullable=True)
    caracteres_compactados: Mapped[int | None] = mapped_column(nullable=True)

    texto_original_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    texto_compactado_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    preview_original: Mapped[str | None] = mapped_column(String(200), nullable=True)
    preview_compactado: Mapped[str | None] = mapped_column(String(200), nullable=True)

    quantidade_alteracoes: Mapped[int] = mapped_column(default=0)
    risco: Mapped[str] = mapped_column(String(20))

    aprovado: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    aprovado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    compactacao_aplicada: Mapped[bool] = mapped_column(Boolean, default=False)
    fallback_utilizado: Mapped[bool] = mapped_column(Boolean, default=False)

    avisos: Mapped[list | None] = mapped_column(_TipoListaJson, nullable=True)
    alteracoes: Mapped[list | None] = mapped_column(_TipoListaJson, nullable=True)

    sucesso: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    mensagem_erro: Mapped[str | None] = mapped_column(Text, nullable=True)
