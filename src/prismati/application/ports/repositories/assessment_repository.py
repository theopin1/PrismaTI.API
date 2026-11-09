from __future__ import annotations

import uuid
from typing import Protocol, runtime_checkable

from prismati.domain.entities.assessment import Assessment


@runtime_checkable
class IAssessmentRepository(Protocol):
    """Interface (port) para repositório de avaliações."""

    def save(self, assessment: Assessment) -> Assessment:
        """Persiste ou atualiza uma avaliação."""
        ...

    def find_by_id(self, assessment_id: uuid.UUID) -> Assessment | None:
        """Busca avaliação pelo ID."""
        ...

    def find_active_by_company(self, company_id: uuid.UUID) -> Assessment | None:
        """Retorna a avaliação em andamento de uma empresa, se existir.
        
        Usado para garantir que uma empresa tenha no máximo uma avaliação ativa.
        """
        ...

    def list_by_company(self, company_id: uuid.UUID) -> list[Assessment]:
        """Lista todas as avaliações de uma empresa."""
        ...

    def list_all(self, skip: int = 0, limit: int = 100) -> list[Assessment]:
        """Lista todas as avaliações com paginação (uso admin)."""
        ...
