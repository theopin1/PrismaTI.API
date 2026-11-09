from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from prismati.domain.enums.status import EvidenceType, EvidenceStatus


@dataclass
class CreateEvidenceDTO:
    """Dados de entrada para criação de evidência."""

    avaliacao_id: uuid.UUID
    pergunta_id: uuid.UUID
    enviado_por: uuid.UUID
    tipo: EvidenceType
    # Para LINK: a URL; para FILE: nome original do arquivo (o storage_path vem do upload)
    referencia: str
    nome_original: str = ""


@dataclass
class EvidenceOutputDTO:
    """Dados de saída de uma evidência."""

    id: uuid.UUID
    avaliacao_id: uuid.UUID
    pergunta_id: uuid.UUID
    tipo: EvidenceType
    status: EvidenceStatus
    referencia: str
    nome_original: str
    criado_em: datetime
    # URL pré-assinada gerada pelo storage para download (apenas para FILE)
    download_url: str | None = None
