"""Base declarativa do SQLAlchemy 2 utilizada por todos os modelos."""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base declarativa compartilhada pelos modelos da plataforma."""
