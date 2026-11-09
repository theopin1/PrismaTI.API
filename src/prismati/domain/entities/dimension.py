from __future__ import annotations

import uuid
from dataclasses import dataclass, field


@dataclass
class Dimension:
    """Entidade de domínio que representa uma dimensão de avaliação (ex.: Governança, Segurança)."""

    versao_questionario_id: uuid.UUID
    nome: str
    descricao: str
    ordem: int
    codigo: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
