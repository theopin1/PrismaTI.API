from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from prismati.domain.enums.status import InvitationStatus
from prismati.domain.exceptions.domain_exceptions import BusinessRuleError


# Validade padrão de um convite em horas
_DEFAULT_EXPIRY_HOURS = 72


@dataclass
class Invitation:
    """Entidade de domínio que representa um convite de acesso enviado por e-mail."""

    email: str
    empresa_id: uuid.UUID
    convidado_por_usuario_id: uuid.UUID
    token: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    status: InvitationStatus = InvitationStatus.PENDING
    criado_em: datetime = field(default_factory=datetime.utcnow)
    expira_em: datetime = field(init=False)
    usuario_id: uuid.UUID | None = None  # preenchido ao aceitar

    def __post_init__(self) -> None:
        self.expira_em = self.criado_em + timedelta(hours=_DEFAULT_EXPIRY_HOURS)

    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expira_em

    @property
    def is_pending(self) -> bool:
        return self.status == InvitationStatus.PENDING

    def accept(self, usuario_id: uuid.UUID) -> None:
        """Marca o convite como aceito e vincula o usuário criado."""
        if self.status != InvitationStatus.PENDING:
            raise BusinessRuleError(f"Convite não pode ser aceito pois está com status '{self.status}'.")
        if self.is_expired:
            raise BusinessRuleError("Convite expirado. Solicite o reenvio.")
        self.status = InvitationStatus.ACCEPTED
        self.usuario_id = usuario_id

    def revoke(self) -> None:
        """Revoga o convite impedindo seu uso."""
        if self.status != InvitationStatus.PENDING:
            raise BusinessRuleError(f"Apenas convites pendentes podem ser revogados. Status atual: '{self.status}'.")
        self.status = InvitationStatus.REVOKED

    def resend(self, new_token: str) -> None:
        """Renova o token e a data de expiração para reenvio."""
        if self.status == InvitationStatus.ACCEPTED:
            raise BusinessRuleError("Convite já aceito não pode ser reenviado.")
        if self.status == InvitationStatus.REVOKED:
            raise BusinessRuleError("Convite revogado não pode ser reenviado.")
        self.token = new_token
        self.status = InvitationStatus.PENDING
        self.criado_em = datetime.utcnow()
        self.expira_em = self.criado_em + timedelta(hours=_DEFAULT_EXPIRY_HOURS)
