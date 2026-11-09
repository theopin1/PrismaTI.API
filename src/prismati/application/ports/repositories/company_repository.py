from __future__ import annotations

import uuid
from typing import Protocol, runtime_checkable

from prismati.domain.entities.company import Company


@runtime_checkable
class ICompanyRepository(Protocol):
    """Interface (port) para repositório de empresas."""

    def save(self, company: Company) -> Company:
        """Persiste ou atualiza uma empresa. Retorna a entidade atualizada."""
        ...

    def find_by_id(self, company_id: uuid.UUID) -> Company | None:
        """Busca empresa pelo ID. Retorna None se não encontrada."""
        ...

    def find_by_cnpj(self, cnpj: str) -> Company | None:
        """Busca empresa pelo CNPJ. Retorna None se não encontrada."""
        ...

    def list_all(self, skip: int = 0, limit: int = 100) -> list[Company]:
        """Lista todas as empresas com paginação."""
        ...

    def delete(self, company_id: uuid.UUID) -> None:
        """Remove uma empresa (uso restrito)."""
        ...
