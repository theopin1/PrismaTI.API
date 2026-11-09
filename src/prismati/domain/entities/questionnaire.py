from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime

from prismati.domain.exceptions.domain_exceptions import BusinessRuleError


class QuestionnaireStatus(str):
    """Status de um questionário ou versão (simples str constants para evitar import circular)."""

    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


@dataclass
class Questionnaire:
    """Entidade de domínio que representa um questionário de avaliação de maturidade."""

    nome: str
    descricao: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    status: str = "DRAFT"

    def publish(self) -> None:
        if self.status == "PUBLISHED":
            raise BusinessRuleError("Questionário já está publicado.")
        self.status = "PUBLISHED"

    def archive(self) -> None:
        self.status = "ARCHIVED"


@dataclass
class QuestionnaireVersion:
    """Entidade de domínio que representa uma versão de questionário."""

    questionario_id: uuid.UUID
    versao: str
    versao_metodologia: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    status: str = "DRAFT"
    publicado_em: datetime | None = None

    def publish(self) -> None:
        """Publica a versão tornando-a disponível para novas avaliações."""
        if self.status == "PUBLISHED":
            raise BusinessRuleError("Esta versão já está publicada.")
        if self.status == "ARCHIVED":
            raise BusinessRuleError("Uma versão arquivada não pode ser publicada.")
        self.status = "PUBLISHED"
        self.publicado_em = datetime.utcnow()

    def archive(self) -> None:
        """Arquiva a versão impedindo novas avaliações com ela."""
        if self.status == "ARCHIVED":
            raise BusinessRuleError("Versão já está arquivada.")
        self.status = "ARCHIVED"

    @property
    def is_published(self) -> bool:
        return self.status == "PUBLISHED"

    @property
    def is_draft(self) -> bool:
        return self.status == "DRAFT"
