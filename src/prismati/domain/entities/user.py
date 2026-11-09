from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime

from prismati.domain.enums.status import UserStatus, UserRole
from prismati.domain.exceptions.domain_exceptions import BusinessRuleError


@dataclass
class User:
    """Entidade de domínio que representa um usuário da plataforma."""

    nome: str
    email: str
    senha_hash: str
    role: UserRole
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    status: UserStatus = UserStatus.PENDING
    data_criacao: datetime = field(default_factory=datetime.utcnow)

    def activate(self) -> None:
        """Ativa o usuário (executado ao aceitar o convite)."""
        if self.status == UserStatus.INACTIVE:
            raise BusinessRuleError("Usuário inativado não pode ser ativado por este fluxo. Contate o administrador.")
        self.status = UserStatus.ACTIVE

    def deactivate(self) -> None:
        """Desativa o usuário impedindo login."""
        self.status = UserStatus.INACTIVE

    def update_status(self, new_status: UserStatus) -> None:
        """Atualiza o status do usuário."""
        self.status = new_status

    def update_password(self, new_senha_hash: str) -> None:
        """Substitui o hash da senha (fluxo de reset)."""
        if not new_senha_hash:
            raise BusinessRuleError("Hash de senha não pode ser vazio.")
        self.senha_hash = new_senha_hash

    @property
    def is_active(self) -> bool:
        return self.status == UserStatus.ACTIVE

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN

    @property
    def is_manager(self) -> bool:
        return self.role == UserRole.MANAGER
