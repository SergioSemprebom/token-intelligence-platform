"""Modelo da tabela `processamentos`, histórico das operações da plataforma."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import JSON, Boolean, DateTime, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.database.base import Base

TIPO_OPERACAO_ANALISE = "analise"
TIPO_OPERACAO_DIVISAO = "divisao"
TIPO_OPERACAO_COMPARACAO = "comparacao"
TIPO_OPERACAO_ESTIMATIVA_CUSTO = "estimativa_custo"
TIPO_OPERACAO_AUDITORIA_PROMPT = "auditoria_prompt"
TIPO_OPERACAO_COMPACTACAO_PROMPT = "compactacao_prompt"
TIPO_OPERACAO_COMPARACAO_COMPACTACAO = "comparacao_compactacao"

TIPOS_OPERACAO_VALIDOS = {
    TIPO_OPERACAO_ANALISE,
    TIPO_OPERACAO_DIVISAO,
    TIPO_OPERACAO_COMPARACAO,
    TIPO_OPERACAO_ESTIMATIVA_CUSTO,
    TIPO_OPERACAO_AUDITORIA_PROMPT,
    TIPO_OPERACAO_COMPACTACAO_PROMPT,
    TIPO_OPERACAO_COMPARACAO_COMPACTACAO,
}

ORIGEM_API = "api"
ORIGEM_CLI = "cli"

ORIGENS_VALIDAS = {ORIGEM_API, ORIGEM_CLI}

# JSON genérico que se torna JSONB no PostgreSQL, mantendo compatibilidade
# explícita (não escondida) com bancos que não suportam JSONB, como o
# SQLite utilizado nos testes unitários.
_TipoMetadados = JSON().with_variant(JSONB, "postgresql")


class Processamento(Base):
    """Registro histórico de uma operação executada pela plataforma."""

    __tablename__ = "processamentos"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    tipo_operacao: Mapped[str] = mapped_column(String(50), index=True)
    origem: Mapped[str] = mapped_column(String(20), index=True)

    modelo_solicitado: Mapped[str | None] = mapped_column(
        String(100), nullable=True, index=True
    )
    encoding_utilizado: Mapped[str | None] = mapped_column(String(100), nullable=True)
    fallback_utilizado: Mapped[bool] = mapped_column(Boolean, default=False)

    caracteres: Mapped[int | None] = mapped_column(nullable=True)
    palavras: Mapped[int | None] = mapped_column(nullable=True)
    bytes_utf8: Mapped[int | None] = mapped_column(nullable=True)

    tokens_entrada: Mapped[int] = mapped_column(default=0)
    tokens_saida: Mapped[int] = mapped_column(default=0)
    total_tokens: Mapped[int] = mapped_column(default=0)

    quantidade_blocos: Mapped[int | None] = mapped_column(nullable=True)
    limite_tokens_bloco: Mapped[int | None] = mapped_column(nullable=True)
    sobreposicao_tokens: Mapped[int | None] = mapped_column(nullable=True)

    custo_entrada: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    custo_saida: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    custo_total: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    moeda: Mapped[str | None] = mapped_column(String(10), nullable=True)

    tempo_processamento_ms: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4), nullable=True
    )

    texto_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    texto_preview: Mapped[str | None] = mapped_column(String(200), nullable=True)

    sucesso: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    mensagem_erro: Mapped[str | None] = mapped_column(Text, nullable=True)

    metadados: Mapped[dict | None] = mapped_column(_TipoMetadados, nullable=True)
