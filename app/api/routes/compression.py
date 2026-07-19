"""Rotas de auditoria e compactação local de prompts (Fase 7).

Nenhuma rota chama IA externa: todas as regras são locais (ver
app/core/text_normalizer.py, app/core/protected_terms.py e
app/config/compression_rules.json). A substituição do texto original nunca é
automática — o texto compactado é sempre uma sugestão, aprovada explicitamente
via POST /api/v1/prompts/aprovar.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import obter_sessao_bd
from app.repositories.compactacao_prompt_repository import CompactacaoPromptRepository
from app.schemas.compression_schemas import (
    AprovarCompactacaoRequest,
    AprovarCompactacaoResponse,
    AuditarPromptRequest,
    AuditarPromptResponse,
    CompactarPromptRequest,
    CompactarPromptResponse,
    CompararCompactacaoRequest,
    CompararCompactacaoResponse,
    ResumoNivelResponse,
    alteracoes_para_schema,
)
from app.services.compression_comparator import comparar_niveis
from app.services.processing_history import (
    registrar_auditoria_prompt,
    registrar_comparacao_compactacao,
    registrar_compactacao_prompt,
)
from app.services.prompt_auditor import auditar_prompt
from app.services.prompt_compressor import compactar_prompt

router = APIRouter(prefix="/api/v1/prompts", tags=["Prompts"])


@router.post(
    "/auditar",
    response_model=AuditarPromptResponse,
    summary="Audita um prompt e identifica possíveis desperdícios, sem alterá-lo",
)
def auditar(
    requisicao: AuditarPromptRequest,
    sessao: Session = Depends(obter_sessao_bd),
) -> AuditarPromptResponse:
    """Executa a auditoria reutilizando app/services/prompt_auditor.py."""
    resultado = auditar_prompt(
        texto=requisicao.texto,
        modelo=requisicao.modelo,
        termos_protegidos=requisicao.termos_protegidos,
    )

    registrar_auditoria_prompt(sessao=sessao, texto=requisicao.texto, resultado=resultado)

    return AuditarPromptResponse(**resultado)


@router.post(
    "/compactar",
    response_model=CompactarPromptResponse,
    summary="Compacta um prompt localmente e retorna uma sugestão (não substitui automaticamente)",
)
def compactar(
    requisicao: CompactarPromptRequest,
    sessao: Session = Depends(obter_sessao_bd),
) -> CompactarPromptResponse:
    """Executa a compactação reutilizando app/services/prompt_compressor.py.

    O texto compactado nunca substitui o original automaticamente: o
    identificador retornado (`compactacao_id`) deve ser enviado a
    POST /api/v1/prompts/aprovar para que o usuário registre sua aprovação.
    """
    resultado = compactar_prompt(
        texto=requisicao.texto,
        nivel=requisicao.nivel,
        modelo=requisicao.modelo,
        termos_protegidos=requisicao.termos_protegidos,
    )

    compactacao_persistida = registrar_compactacao_prompt(sessao=sessao, resultado=resultado)
    compactacao_id = compactacao_persistida.id if compactacao_persistida else uuid.uuid4()

    return CompactarPromptResponse(
        compactacao_id=compactacao_id,
        texto_original=resultado.texto_original,
        texto_compactado=resultado.texto_compactado,
        nivel=resultado.nivel,
        modelo=resultado.modelo,
        encoding=resultado.encoding,
        tokens_originais=resultado.tokens_originais,
        tokens_compactados=resultado.tokens_compactados,
        tokens_economizados=resultado.tokens_economizados,
        reducao_percentual=resultado.reducao_percentual,
        caracteres_originais=resultado.caracteres_originais,
        caracteres_compactados=resultado.caracteres_compactados,
        alteracoes_aplicadas=alteracoes_para_schema(resultado.alteracoes_aplicadas),
        termos_protegidos=resultado.termos_protegidos,
        avisos=resultado.avisos,
        risco=resultado.risco,
        fallback_utilizado=resultado.fallback_utilizado,
        compactacao_aplicada=resultado.compactacao_aplicada,
        aprovado=False,
    )


@router.post(
    "/comparar-compactacao",
    response_model=CompararCompactacaoResponse,
    summary="Compara os três níveis de compactação para o mesmo texto",
)
def comparar_compactacao(
    requisicao: CompararCompactacaoRequest,
    sessao: Session = Depends(obter_sessao_bd),
) -> CompararCompactacaoResponse:
    """Compara os níveis reutilizando app/services/compression_comparator.py."""
    resultado = comparar_niveis(
        texto=requisicao.texto,
        modelo=requisicao.modelo,
        termos_protegidos=requisicao.termos_protegidos,
    )

    registrar_comparacao_compactacao(sessao=sessao, texto=requisicao.texto, resultado=resultado)

    return CompararCompactacaoResponse(
        modelo=resultado["modelo"],
        encoding=resultado["encoding"],
        fallback_utilizado=resultado["fallback_utilizado"],
        tokens_originais=resultado["tokens_originais"],
        resultados=[ResumoNivelResponse(**item) for item in resultado["resultados"]],
        melhor_reducao=resultado["melhor_reducao"],
        recomendado=resultado["recomendado"],
        avisos=resultado["avisos"],
    )


@router.post(
    "/aprovar",
    response_model=AprovarCompactacaoResponse,
    summary="Registra a aprovação humana de uma compactação já gerada",
)
def aprovar(
    requisicao: AprovarCompactacaoRequest,
    sessao: Session = Depends(obter_sessao_bd),
) -> AprovarCompactacaoResponse:
    """Marca uma compactação existente como aprovada. Não chama IA externa."""
    compactacao = CompactacaoPromptRepository(sessao).aprovar(requisicao.compactacao_id)

    if compactacao is None:
        raise HTTPException(status_code=404, detail="Compactação não encontrada.")

    return AprovarCompactacaoResponse(
        compactacao_id=compactacao.id,
        aprovado=compactacao.aprovado,
        aprovado_em=compactacao.aprovado_em,
    )
