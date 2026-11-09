from __future__ import annotations

import uuid
from typing import Protocol, runtime_checkable

from prismati.domain.entities.user import User
from prismati.domain.entities.company_membership import CompanyMembership


@runtime_checkable
class IUserRepository(Protocol):
    """Interface (port) para repositório de usuários."""

    def save(self, user: User) -> User:
        """Persiste ou atualiza um usuário."""
        ...

    def find_by_id(self, user_id: uuid.UUID) -> User | None:
        """Busca usuário pelo ID."""
        ...

    def find_by_email(self, email: str) -> User | None:
        """Busca usuário pelo e-mail (usado no login)."""
        ...

    def list_all(self, skip: int = 0, limit: int = 100) -> list[User]:
        """Lista todos os usuários com paginação."""
        ...

    def save_membership(self, membership: CompanyMembership) -> CompanyMembership:
        """Persiste o vínculo usuário ↔ empresa."""
        ...

    def find_membership_by_user(self, user_id: uuid.UUID) -> CompanyMembership | None:
        """Retorna o vínculo de empresa do usuário, se existir."""
        ...

    def find_membership_by_company(self, company_id: uuid.UUID) -> list[CompanyMembership]:
        """Retorna todos os vínculos de uma empresa."""
        ...
