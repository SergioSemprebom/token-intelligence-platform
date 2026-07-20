"""Endpoints do dashboard web da Fase 8.

A primeira entrega usa dados demonstrativos padronizados. Nas próximas entregas,
esses dados serão substituídos pelos conectores reais dos provedores.
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])


@router.get("/resumo", summary="Resumo consolidado da plataforma")
def obter_resumo() -> dict:
    """Retorna os indicadores necessários para a tela inicial."""
    return {
        "periodo": date.today().strftime("%Y-%m"),
        "moeda": "USD",
        "gasto_mes": 42.70,
        "orcamento_mensal": 100.00,
        "projecao_mes": 67.30,
        "tokens_total": 8_420_500,
        "requisicoes_total": 12_480,
        "economia_estimada": 18.40,
        "provedores": [
            {
                "nome": "OpenAI",
                "slug": "openai",
                "status": "demonstracao",
                "tokens": 3_200_000,
                "requisicoes": 4_850,
                "custo": 18.60,
            },
            {
                "nome": "Gemini",
                "slug": "gemini",
                "status": "planejado",
                "tokens": 2_900_000,
                "requisicoes": 5_100,
                "custo": 8.20,
            },
            {
                "nome": "Claude",
                "slug": "anthropic",
                "status": "planejado",
                "tokens": 1_800_000,
                "requisicoes": 1_930,
                "custo": 14.70,
            },
            {
                "nome": "OpenRouter",
                "slug": "openrouter",
                "status": "planejado",
                "tokens": 520_500,
                "requisicoes": 600,
                "custo": 1.20,
            },
        ],
        "consumo_diario": [
            {"dia": "01", "custo": 3.20},
            {"dia": "05", "custo": 5.10},
            {"dia": "10", "custo": 6.80},
            {"dia": "15", "custo": 8.40},
            {"dia": "20", "custo": 9.70},
            {"dia": "25", "custo": 9.50},
        ],
    }


@router.get("/provedores", summary="Lista provedores suportados")
def listar_provedores() -> list[dict[str, str]]:
    """Expõe o catálogo inicial de integrações da plataforma."""
    return [
        {"nome": "OpenAI", "slug": "openai", "status": "disponivel_em_breve"},
        {"nome": "Gemini", "slug": "gemini", "status": "planejado"},
        {"nome": "Claude", "slug": "anthropic", "status": "planejado"},
        {"nome": "OpenRouter", "slug": "openrouter", "status": "planejado"},
    ]
