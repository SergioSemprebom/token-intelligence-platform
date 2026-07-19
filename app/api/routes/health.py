"""Rota de verificação de saúde da aplicação."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["Saúde"])


@router.get(
    "/health",
    summary="Verifica a saúde da aplicação",
    response_description="Status atual da aplicação.",
)
def verificar_saude() -> dict[str, str]:
    """Retorna o status atual da aplicação."""
    return {"status": "ok"}
