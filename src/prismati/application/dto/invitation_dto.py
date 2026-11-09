from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from prismati.domain.enums.status import InvitationStatus


@dataclass
class CreateInvitationDTO:
    """Dados de entrada para envio de convite de acesso."""

    email: str
    empresa_id: uuid.UUID
    convidado_por_usuario_id: uuid.UUID


@dataclass
class InvitationOutputDTO:
    """Dados de saída de um convite para a camada de apresentação."""

    id: uuid.UUID
    email: str
    empresa_id: uuid.UUID
    status: InvitationStatus
    criado_em: datetime
    expira_em: datetime
    usuario_id: uuid.UUID | None = None
