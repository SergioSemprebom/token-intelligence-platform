"""Acesso a dados da tabela `compactacoes_prompt`, sem regras de negócio."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.database.models.compactacao_prompt import CompactacaoPrompt


class CompactacaoPromptRepository:
    """Repositório de acesso a dados para compactações de prompt."""

    def __init__(self, sessao: Session) -> None:
        self._sessao = sessao

    def criar(self, compactacao: CompactacaoPrompt) -> CompactacaoPrompt:
        """Persiste um novo registro de compactação de prompt."""
        self._sessao.add(compactacao)
        self._sessao.commit()
        self._sessao.refresh(compactacao)
        return compactacao

    def buscar_por_id(self, compactacao_id: uuid.UUID) -> CompactacaoPrompt | None:
        """Busca uma compactação pelo identificador. Retorna None se não existir."""
        return self._sessao.get(CompactacaoPrompt, compactacao_id)

    def aprovar(self, compactacao_id: uuid.UUID) -> CompactacaoPrompt | None:
        """Marca uma compactação como aprovada pelo usuário. Retorna None se não existir."""
        compactacao = self.buscar_por_id(compactacao_id)

        if compactacao is None:
            return None

        compactacao.aprovado = True
        compactacao.aprovado_em = datetime.now(timezone.utc)
        self._sessao.commit()
        self._sessao.refresh(compactacao)
        return compactacao
