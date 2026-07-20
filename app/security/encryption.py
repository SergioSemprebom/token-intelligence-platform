"""Criptografia de credenciais de provedores com Fernet."""

from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken

from app.config.settings import obter_configuracoes


def _fernet() -> Fernet:
    chave = obter_configuracoes().provider_encryption_key
    if not chave:
        raise RuntimeError("PROVIDER_ENCRYPTION_KEY não foi configurada.")
    return Fernet(chave.encode("utf-8"))


def criptografar(valor: str) -> str:
    return _fernet().encrypt(valor.encode("utf-8")).decode("utf-8")


def descriptografar(valor: str) -> str:
    try:
        return _fernet().decrypt(valor.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise RuntimeError("Não foi possível descriptografar a credencial.") from exc
