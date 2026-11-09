from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class CompanyMembership:
    """Entidade de domínio que representa o vínculo entre usuário e empresa (VinculoEmpresa).

    Um usuário pode estar vinculado a uma única empresa como gestor de TI.
    """

    empresa_id: uuid.UUID
    usuario_id: uuid.UUID
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    criado_em: datetime = field(default_factory=datetime.utcnow)
