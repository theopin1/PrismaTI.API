from __future__ import annotations

import uuid
from typing import Protocol, runtime_checkable

from prismati.domain.entities.invitation import Invitation


@runtime_checkable
class IInvitationRepository(Protocol):
    """Interface (port) para repositório de convites."""

    def save(self, invitation: Invitation) -> Invitation:
        """Persiste ou atualiza um convite."""
        ...

    def find_by_id(self, invitation_id: uuid.UUID) -> Invitation | None:
        """Busca convite pelo ID."""
        ...

    def find_by_token(self, token: str) -> Invitation | None:
        """Busca convite pelo token (usado na ativação)."""
        ...

    def find_by_email(self, email: str) -> Invitation | None:
        """Retorna convite pendente para o e-mail, se existir."""
        ...

    def list_by_company(self, company_id: uuid.UUID) -> list[Invitation]:
        """Lista convites de uma empresa."""
        ...
