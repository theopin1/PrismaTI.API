from __future__ import annotations

import uuid
from typing import Protocol, runtime_checkable

from prismati.domain.entities.result import AssessmentResult, DimensionResult


@runtime_checkable
class IResultRepository(Protocol):
    """Interface (port) para repositório de resultados de avaliação."""

    def save(self, result: AssessmentResult) -> AssessmentResult:
        """Persiste o resultado calculado de uma avaliação."""
        ...

    def find_by_assessment(self, assessment_id: uuid.UUID) -> AssessmentResult | None:
        """Busca o resultado de uma avaliação pelo ID da avaliação."""
        ...
