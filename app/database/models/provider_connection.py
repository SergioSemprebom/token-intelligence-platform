"""Conexões criptografadas com provedores de IA."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.database.base import Base


class ProviderConnection(Base):
    __tablename__ = "provider_connections"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_slug: Mapped[str] = mapped_column(String(50), index=True)
    nome: Mapped[str] = mapped_column(String(80))
    encrypted_api_key: Mapped[str] = mapped_column(Text)
    credential_hint: Mapped[str] = mapped_column(String(40))
    orcamento_mensal: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=100)
    moeda: Mapped[str] = mapped_column(String(3), default="USD")
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    ultima_sincronizacao_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ultimo_status: Mapped[str] = mapped_column(String(40), default="conectado")
    ultimo_erro: Mapped[str | None] = mapped_column(Text, nullable=True)
