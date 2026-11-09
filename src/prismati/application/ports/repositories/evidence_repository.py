from __future__ import annotations

import uuid
from typing import Protocol, runtime_checkable

from prismati.domain.entities.evidence import Evidence


@runtime_checkable
class IEvidenceRepository(Protocol):
    """Interface (port) para repositório de evidências."""

    def save(self, evidence: Evidence) -> Evidence:
        """Persiste ou atualiza uma evidência."""
        ...

    def find_by_id(self, evidence_id: uuid.UUID) -> Evidence | None:
        """Busca evidência pelo ID."""
        ...

    def list_by_assessment(self, assessment_id: uuid.UUID) -> list[Evidence]:
        """Lista todas as evidências ativas de uma avaliação."""
        ...

    def list_by_question(self, assessment_id: uuid.UUID, question_id: uuid.UUID) -> list[Evidence]:
        """Lista evidências ativas de uma pergunta específica em uma avaliação."""
        ...
