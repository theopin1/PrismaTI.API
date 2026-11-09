from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime

from prismati.domain.enums.status import EvidenceType, EvidenceStatus


@dataclass
class Evidence:
    """Entidade de domínio que representa uma evidência anexada a uma resposta.

    Pode ser um arquivo enviado (upload) ou um link externo.
    """

    avaliacao_id: uuid.UUID
    pergunta_id: uuid.UUID
    enviado_por: uuid.UUID
    tipo: EvidenceType
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    status: EvidenceStatus = EvidenceStatus.ACTIVE
    # Para FILE: caminho no storage; para LINK: URL
    referencia: str = ""
    nome_original: str = ""
    criado_em: datetime = field(default_factory=datetime.utcnow)

    def delete(self) -> None:
        """Marca a evidência como deletada (soft delete)."""
        self.status = EvidenceStatus.DELETED

    @property
    def is_active(self) -> bool:
        return self.status == EvidenceStatus.ACTIVE

    @property
    def is_file(self) -> bool:
        return self.tipo == EvidenceType.FILE

    @property
    def is_link(self) -> bool:
        return self.tipo == EvidenceType.LINK
