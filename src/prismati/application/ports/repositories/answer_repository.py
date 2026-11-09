from __future__ import annotations

import uuid
from typing import Protocol, runtime_checkable

from prismati.domain.entities.answer import Answer


@runtime_checkable
class IAnswerRepository(Protocol):
    """Interface (port) para repositório de respostas de avaliação."""

    def save(self, answer: Answer) -> Answer:
        """Persiste ou atualiza uma resposta (upsert por avaliacao_id + pergunta_id)."""
        ...

    def find_by_id(self, answer_id: uuid.UUID) -> Answer | None:
        """Busca resposta pelo ID."""
        ...

    def find_by_assessment_and_question(
        self, assessment_id: uuid.UUID, question_id: uuid.UUID
    ) -> Answer | None:
        """Busca a resposta de uma pergunta específica em uma avaliação."""
        ...

    def list_by_assessment(self, assessment_id: uuid.UUID) -> list[Answer]:
        """Lista todas as respostas de uma avaliação."""
        ...

    def count_by_assessment(self, assessment_id: uuid.UUID) -> int:
        """Conta o total de respostas salvas para uma avaliação."""
        ...
