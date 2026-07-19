"""Transforma resultados das operações da plataforma em histórico persistido.

Por padrão, o texto completo processado nunca é armazenado: apenas o
SHA-256 (`texto_hash`) e os primeiros caracteres (`texto_preview`). A
configuração `SALVAR_TEXTO_COMPLETO` existe para preparar uma futura coluna
de texto completo, mas essa coluna ainda não foi criada nesta fase.
"""

from __future__ import annotations

import hashlib
import logging
from decimal import Decimal
from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database.models.compactacao_prompt import CompactacaoPrompt
from app.database.models.processamento import (
    ORIGEM_API,
    TIPO_OPERACAO_ANALISE,
    TIPO_OPERACAO_AUDITORIA_PROMPT,
    TIPO_OPERACAO_COMPARACAO,
    TIPO_OPERACAO_COMPARACAO_COMPACTACAO,
    TIPO_OPERACAO_COMPACTACAO_PROMPT,
    TIPO_OPERACAO_DIVISAO,
    TIPO_OPERACAO_ESTIMATIVA_CUSTO,
    Processamento,
)
from app.repositories.compactacao_prompt_repository import CompactacaoPromptRepository
from app.repositories.processamento_repository import ProcessamentoRepository
from app.services.model_comparator import ResultadoComparacaoModelo
from app.services.prompt_compressor import ResultadoCompactacaoPrompt

logger = logging.getLogger(__name__)

TAMANHO_PREVIEW = 200


def calcular_hash_texto(texto: str) -> str:
    """Calcula o SHA-256 do texto normalizado, sem armazenar o conteúdo original."""
    return hashlib.sha256(texto.strip().encode("utf-8")).hexdigest()


def calcular_preview_texto(texto: str, tamanho: int = TAMANHO_PREVIEW) -> str:
    """Retorna apenas os primeiros caracteres do texto normalizado."""
    return texto.strip()[:tamanho]


def _persistir(sessao: Session, processamento: Processamento) -> Processamento | None:
    """Persiste um processamento sem deixar falha de banco derrubar a operação principal."""
    try:
        return ProcessamentoRepository(sessao).criar(processamento)
    except SQLAlchemyError:
        logger.error(
            "Falha ao persistir histórico de processamento (tipo_operacao=%s); "
            "o histórico não foi salvo, mas o resultado principal foi mantido.",
            processamento.tipo_operacao,
            exc_info=True,
        )
        return None


def registrar_analise(
    sessao: Session,
    texto: str,
    resultado: dict[str, Any],
    fallback_utilizado: bool,
    origem: str = ORIGEM_API,
) -> Processamento | None:
    """Registra o histórico de uma operação de análise de texto."""
    tokens = resultado["tokens"]
    processamento = Processamento(
        tipo_operacao=TIPO_OPERACAO_ANALISE,
        origem=origem,
        modelo_solicitado=resultado["modelo"],
        encoding_utilizado=resultado["encoding"],
        fallback_utilizado=fallback_utilizado,
        caracteres=resultado["caracteres"],
        palavras=resultado["palavras"],
        bytes_utf8=resultado["bytes_utf8"],
        tokens_entrada=tokens,
        tokens_saida=0,
        total_tokens=tokens,
        tempo_processamento_ms=Decimal(str(resultado["tempo_processamento_ms"])),
        texto_hash=calcular_hash_texto(texto),
        texto_preview=calcular_preview_texto(texto),
        sucesso=True,
    )
    return _persistir(sessao, processamento)


def registrar_divisao(
    sessao: Session,
    texto: str,
    modelo: str,
    limite_tokens: int,
    sobreposicao_tokens: int,
    total_blocos: int,
    total_tokens_original: int,
    origem: str = ORIGEM_API,
) -> Processamento | None:
    """Registra o histórico de uma operação de divisão de texto por tokens."""
    processamento = Processamento(
        tipo_operacao=TIPO_OPERACAO_DIVISAO,
        origem=origem,
        modelo_solicitado=modelo,
        tokens_entrada=total_tokens_original,
        tokens_saida=0,
        total_tokens=total_tokens_original,
        quantidade_blocos=total_blocos,
        limite_tokens_bloco=limite_tokens,
        sobreposicao_tokens=sobreposicao_tokens,
        texto_hash=calcular_hash_texto(texto),
        texto_preview=calcular_preview_texto(texto),
        sucesso=True,
    )
    return _persistir(sessao, processamento)


def registrar_comparacao(
    sessao: Session,
    texto: str,
    resultados: list[ResultadoComparacaoModelo],
    origem: str = ORIGEM_API,
) -> list[Processamento]:
    """Registra o histórico de uma comparação, um processamento por modelo comparado."""
    texto_hash = calcular_hash_texto(texto)
    texto_preview = calcular_preview_texto(texto)
    registrados: list[Processamento] = []

    for resultado in resultados:
        processamento = Processamento(
            tipo_operacao=TIPO_OPERACAO_COMPARACAO,
            origem=origem,
            modelo_solicitado=resultado.modelo_solicitado,
            encoding_utilizado=resultado.encoding_utilizado,
            fallback_utilizado=resultado.fallback_utilizado,
            caracteres=resultado.caracteres,
            palavras=resultado.palavras,
            bytes_utf8=resultado.bytes_utf8,
            tokens_entrada=resultado.tokens,
            tokens_saida=0,
            total_tokens=resultado.tokens,
            texto_hash=texto_hash,
            texto_preview=texto_preview,
            sucesso=True,
        )
        persistido = _persistir(sessao, processamento)
        if persistido is not None:
            registrados.append(persistido)

    return registrados


def registrar_estimativa_custo(
    sessao: Session,
    modelo: str,
    tokens_entrada: int,
    tokens_saida: int,
    custo_entrada: Decimal,
    custo_saida: Decimal,
    custo_total: Decimal,
    moeda: str,
    origem: str = ORIGEM_API,
) -> Processamento | None:
    """Registra o histórico de uma estimativa de custo."""
    processamento = Processamento(
        tipo_operacao=TIPO_OPERACAO_ESTIMATIVA_CUSTO,
        origem=origem,
        modelo_solicitado=modelo,
        tokens_entrada=tokens_entrada,
        tokens_saida=tokens_saida,
        total_tokens=tokens_entrada + tokens_saida,
        custo_entrada=custo_entrada,
        custo_saida=custo_saida,
        custo_total=custo_total,
        moeda=moeda,
        sucesso=True,
    )
    return _persistir(sessao, processamento)


def registrar_erro(
    sessao: Session,
    tipo_operacao: str,
    mensagem_erro: str,
    origem: str = ORIGEM_API,
    modelo_solicitado: str | None = None,
    texto: str | None = None,
) -> Processamento | None:
    """Registra o histórico de uma operação que falhou."""
    processamento = Processamento(
        tipo_operacao=tipo_operacao,
        origem=origem,
        modelo_solicitado=modelo_solicitado,
        tokens_entrada=0,
        tokens_saida=0,
        total_tokens=0,
        texto_hash=calcular_hash_texto(texto) if texto else None,
        texto_preview=calcular_preview_texto(texto) if texto else None,
        sucesso=False,
        mensagem_erro=mensagem_erro,
    )
    return _persistir(sessao, processamento)


def registrar_auditoria_prompt(
    sessao: Session,
    texto: str,
    resultado: dict[str, Any],
    origem: str = ORIGEM_API,
) -> Processamento | None:
    """Registra o histórico de uma auditoria de prompt."""
    tokens = resultado["tokens_originais"]
    processamento = Processamento(
        tipo_operacao=TIPO_OPERACAO_AUDITORIA_PROMPT,
        origem=origem,
        modelo_solicitado=resultado["modelo"],
        encoding_utilizado=resultado["encoding"],
        fallback_utilizado=resultado["fallback_utilizado"],
        caracteres=resultado["caracteres"],
        palavras=resultado["palavras"],
        tokens_entrada=tokens,
        tokens_saida=0,
        total_tokens=tokens,
        texto_hash=calcular_hash_texto(texto),
        texto_preview=calcular_preview_texto(texto),
        sucesso=True,
        metadados={
            "nivel_desperdicio": resultado["nivel_desperdicio"],
            "quantidade_problemas": len(resultado["problemas_encontrados"]),
        },
    )
    return _persistir(sessao, processamento)


def _persistir_compactacao(
    sessao: Session, compactacao: CompactacaoPrompt
) -> CompactacaoPrompt | None:
    """Persiste uma compactação de prompt sem derrubar a operação principal em caso de falha."""
    try:
        return CompactacaoPromptRepository(sessao).criar(compactacao)
    except SQLAlchemyError:
        logger.error(
            "Falha ao persistir compactação de prompt (nivel=%s); o histórico não foi "
            "salvo, mas o resultado principal foi mantido.",
            compactacao.nivel_compactacao,
            exc_info=True,
        )
        return None


def registrar_compactacao_prompt(
    sessao: Session,
    resultado: ResultadoCompactacaoPrompt,
    origem: str = ORIGEM_API,
) -> CompactacaoPrompt | None:
    """Registra uma compactação de prompt em `compactacoes_prompt` e em `processamentos`."""
    processamento = Processamento(
        tipo_operacao=TIPO_OPERACAO_COMPACTACAO_PROMPT,
        origem=origem,
        modelo_solicitado=resultado.modelo,
        encoding_utilizado=resultado.encoding,
        fallback_utilizado=resultado.fallback_utilizado,
        caracteres=resultado.caracteres_originais,
        tokens_entrada=resultado.tokens_originais,
        tokens_saida=resultado.tokens_compactados,
        total_tokens=resultado.tokens_originais,
        texto_hash=calcular_hash_texto(resultado.texto_original),
        texto_preview=calcular_preview_texto(resultado.texto_original),
        sucesso=True,
        metadados={
            "nivel_compactacao": resultado.nivel,
            "compactacao_aplicada": resultado.compactacao_aplicada,
        },
    )
    processamento_persistido = _persistir(sessao, processamento)

    compactacao = CompactacaoPrompt(
        processamento_id=processamento_persistido.id if processamento_persistido else None,
        origem=origem,
        modelo_solicitado=resultado.modelo,
        encoding_utilizado=resultado.encoding,
        nivel_compactacao=resultado.nivel,
        tokens_originais=resultado.tokens_originais,
        tokens_compactados=resultado.tokens_compactados,
        tokens_economizados=resultado.tokens_economizados,
        reducao_percentual=Decimal(str(resultado.reducao_percentual)),
        caracteres_originais=resultado.caracteres_originais,
        caracteres_compactados=resultado.caracteres_compactados,
        texto_original_hash=calcular_hash_texto(resultado.texto_original),
        texto_compactado_hash=calcular_hash_texto(resultado.texto_compactado),
        preview_original=calcular_preview_texto(resultado.texto_original),
        preview_compactado=calcular_preview_texto(resultado.texto_compactado),
        quantidade_alteracoes=len(resultado.alteracoes_aplicadas),
        risco=resultado.risco,
        compactacao_aplicada=resultado.compactacao_aplicada,
        fallback_utilizado=resultado.fallback_utilizado,
        avisos=resultado.avisos,
        alteracoes=resultado.alteracoes_aplicadas,
        sucesso=True,
    )
    return _persistir_compactacao(sessao, compactacao)


def registrar_comparacao_compactacao(
    sessao: Session,
    texto: str,
    resultado: dict[str, Any],
    origem: str = ORIGEM_API,
) -> Processamento | None:
    """Registra o histórico de uma comparação entre níveis de compactação."""
    processamento = Processamento(
        tipo_operacao=TIPO_OPERACAO_COMPARACAO_COMPACTACAO,
        origem=origem,
        modelo_solicitado=resultado["modelo"],
        encoding_utilizado=resultado["encoding"],
        fallback_utilizado=resultado["fallback_utilizado"],
        tokens_entrada=resultado["tokens_originais"],
        tokens_saida=0,
        total_tokens=resultado["tokens_originais"],
        texto_hash=calcular_hash_texto(texto),
        texto_preview=calcular_preview_texto(texto),
        sucesso=True,
        metadados={
            "melhor_reducao": resultado["melhor_reducao"],
            "recomendado": resultado["recomendado"],
        },
    )
    return _persistir(sessao, processamento)
