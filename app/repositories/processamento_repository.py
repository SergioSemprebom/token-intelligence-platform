"""Acesso a dados da tabela `processamentos`, sem regras de negócio."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.database.models.processamento import Processamento


@dataclass(frozen=True)
class ResumoProcessamentos:
    """Resultado agregado do histórico de processamentos."""

    total_processamentos: int
    total_tokens_entrada: int
    total_tokens_saida: int
    total_tokens: int
    custo_total: Decimal
    quantidade_sucessos: int
    quantidade_erros: int
    processamentos_por_tipo: dict[str, int]
    processamentos_por_modelo: dict[str, int]


class ProcessamentoRepository:
    """Repositório de acesso a dados para o histórico de processamentos."""

    def __init__(self, sessao: Session) -> None:
        self._sessao = sessao

    def criar(self, processamento: Processamento) -> Processamento:
        """Persiste um novo registro de processamento."""
        self._sessao.add(processamento)
        self._sessao.commit()
        self._sessao.refresh(processamento)
        return processamento

    def buscar_por_id(self, processamento_id: uuid.UUID) -> Processamento | None:
        """Busca um processamento pelo identificador. Retorna None se não existir."""
        return self._sessao.get(Processamento, processamento_id)

    def listar(
        self,
        limite: int = 20,
        offset: int = 0,
        tipo_operacao: str | None = None,
        modelo_solicitado: str | None = None,
        sucesso: bool | None = None,
        data_inicio: datetime | None = None,
        data_fim: datetime | None = None,
    ) -> list[Processamento]:
        """Lista processamentos com filtros opcionais, mais recentes primeiro."""
        instrucao = self._aplicar_filtros(
            select(Processamento),
            tipo_operacao=tipo_operacao,
            modelo_solicitado=modelo_solicitado,
            sucesso=sucesso,
            data_inicio=data_inicio,
            data_fim=data_fim,
        )
        instrucao = instrucao.order_by(Processamento.criado_em.desc()).limit(limite).offset(offset)
        return list(self._sessao.execute(instrucao).scalars().all())

    def contar(
        self,
        tipo_operacao: str | None = None,
        modelo_solicitado: str | None = None,
        sucesso: bool | None = None,
        data_inicio: datetime | None = None,
        data_fim: datetime | None = None,
    ) -> int:
        """Conta processamentos que atendem aos filtros opcionais informados."""
        instrucao = self._aplicar_filtros(
            select(func.count(Processamento.id)),
            tipo_operacao=tipo_operacao,
            modelo_solicitado=modelo_solicitado,
            sucesso=sucesso,
            data_inicio=data_inicio,
            data_fim=data_fim,
        )
        return self._sessao.execute(instrucao).scalar_one()

    def listar_por_tipo(
        self, tipo_operacao: str, limite: int = 20, offset: int = 0
    ) -> list[Processamento]:
        """Lista processamentos de um tipo de operação específico."""
        return self.listar(limite=limite, offset=offset, tipo_operacao=tipo_operacao)

    def listar_por_periodo(
        self,
        data_inicio: datetime,
        data_fim: datetime,
        limite: int = 20,
        offset: int = 0,
    ) -> list[Processamento]:
        """Lista processamentos criados dentro de um período específico."""
        return self.listar(
            limite=limite, offset=offset, data_inicio=data_inicio, data_fim=data_fim
        )

    def obter_resumo(self) -> ResumoProcessamentos:
        """Calcula métricas agregadas de todo o histórico de processamentos."""
        linha = self._sessao.execute(
            select(
                func.count(Processamento.id),
                func.coalesce(func.sum(Processamento.tokens_entrada), 0),
                func.coalesce(func.sum(Processamento.tokens_saida), 0),
                func.coalesce(func.sum(Processamento.total_tokens), 0),
                func.coalesce(func.sum(Processamento.custo_total), 0),
                func.coalesce(
                    func.sum(case((Processamento.sucesso.is_(True), 1), else_=0)), 0
                ),
                func.coalesce(
                    func.sum(case((Processamento.sucesso.is_(False), 1), else_=0)), 0
                ),
            )
        ).one()

        por_tipo = dict(
            self._sessao.execute(
                select(Processamento.tipo_operacao, func.count(Processamento.id)).group_by(
                    Processamento.tipo_operacao
                )
            ).all()
        )

        por_modelo = dict(
            self._sessao.execute(
                select(Processamento.modelo_solicitado, func.count(Processamento.id))
                .where(Processamento.modelo_solicitado.is_not(None))
                .group_by(Processamento.modelo_solicitado)
            ).all()
        )

        return ResumoProcessamentos(
            total_processamentos=linha[0],
            total_tokens_entrada=linha[1],
            total_tokens_saida=linha[2],
            total_tokens=linha[3],
            custo_total=Decimal(str(linha[4])),
            quantidade_sucessos=linha[5],
            quantidade_erros=linha[6],
            processamentos_por_tipo=por_tipo,
            processamentos_por_modelo=por_modelo,
        )

    def _aplicar_filtros(
        self,
        instrucao,
        tipo_operacao: str | None,
        modelo_solicitado: str | None,
        sucesso: bool | None,
        data_inicio: datetime | None,
        data_fim: datetime | None,
    ):
        if tipo_operacao is not None:
            instrucao = instrucao.where(Processamento.tipo_operacao == tipo_operacao)
        if modelo_solicitado is not None:
            instrucao = instrucao.where(Processamento.modelo_solicitado == modelo_solicitado)
        if sucesso is not None:
            instrucao = instrucao.where(Processamento.sucesso == sucesso)
        if data_inicio is not None:
            instrucao = instrucao.where(Processamento.criado_em >= data_inicio)
        if data_fim is not None:
            instrucao = instrucao.where(Processamento.criado_em <= data_fim)
        return instrucao
