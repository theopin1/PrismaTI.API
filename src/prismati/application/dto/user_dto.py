from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from prismati.domain.enums.status import UserStatus, UserRole


@dataclass
class CreateUserDTO:
    """Dados de entrada para criação de usuário (somente admin)."""

    nome: str
    email: str
    role: UserRole
    empresa_id: uuid.UUID | None = None  # obrigatório para MANAGER


@dataclass
class UpdateUserStatusDTO:
    """Dados de entrada para alteração de status de usuário."""

    status: UserStatus


@dataclass
class UserOutputDTO:
    """Dados de saída de um usuário para a camada de apresentação."""

    id: uuid.UUID
    nome: str
    email: str
    role: UserRole
    status: UserStatus
    data_criacao: datetime
    empresa_id: uuid.UUID | None = None
