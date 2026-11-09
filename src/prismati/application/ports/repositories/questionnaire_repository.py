from __future__ import annotations

import uuid
from typing import Protocol, runtime_checkable

from prismati.domain.entities.questionnaire import Questionnaire, QuestionnaireVersion
from prismati.domain.entities.dimension import Dimension
from prismati.domain.entities.question import Question, Alternative


@runtime_checkable
class IQuestionnaireRepository(Protocol):
    """Interface (port) para repositório de questionários, versões, dimensões e perguntas."""

    # --- Questionários ---

    def save_questionnaire(self, questionnaire: Questionnaire) -> Questionnaire:
        """Persiste ou atualiza um questionário."""
        ...

    def find_questionnaire_by_id(self, questionnaire_id: uuid.UUID) -> Questionnaire | None:
        """Busca questionário pelo ID."""
        ...

    def list_questionnaires(self) -> list[Questionnaire]:
        """Lista todos os questionários."""
        ...

    # --- Versões ---

    def save_version(self, version: QuestionnaireVersion) -> QuestionnaireVersion:
        """Persiste ou atualiza uma versão de questionário."""
        ...

    def find_version_by_id(self, version_id: uuid.UUID) -> QuestionnaireVersion | None:
        """Busca versão pelo ID."""
        ...

    def list_versions_by_questionnaire(self, questionnaire_id: uuid.UUID) -> list[QuestionnaireVersion]:
        """Lista versões de um questionário."""
        ...

    def find_published_version(self, questionnaire_id: uuid.UUID) -> QuestionnaireVersion | None:
        """Retorna a versão publicada ativa do questionário, se existir."""
        ...

    # --- Dimensões ---

    def save_dimension(self, dimension: Dimension) -> Dimension:
        """Persiste ou atualiza uma dimensão."""
        ...

    def find_dimension_by_id(self, dimension_id: uuid.UUID) -> Dimension | None:
        """Busca dimensão pelo ID."""
        ...

    def list_dimensions_by_version(self, version_id: uuid.UUID) -> list[Dimension]:
        """Lista todas as dimensões de uma versão ordenadas pelo campo 'ordem'."""
        ...

    # --- Perguntas e Alternativas ---

    def save_question(self, question: Question) -> Question:
        """Persiste ou atualiza uma pergunta (incluindo alternativas)."""
        ...

    def find_question_by_id(self, question_id: uuid.UUID) -> Question | None:
        """Busca pergunta pelo ID (com alternativas carregadas)."""
        ...

    def list_questions_by_dimension(self, dimension_id: uuid.UUID) -> list[Question]:
        """Lista perguntas de uma dimensão ordenadas pelo campo 'ordem'."""
        ...

    def list_questions_by_version(self, version_id: uuid.UUID) -> list[Question]:
        """Lista todas as perguntas de uma versão do questionário."""
        ...

    def find_alternative_by_id(self, alternative_id: uuid.UUID) -> Alternative | None:
        """Busca alternativa pelo ID."""
        ...

    def list_alternatives_by_ids(self, alternative_ids: list[uuid.UUID]) -> dict[uuid.UUID, Alternative]:
        """Retorna mapa id → Alternative para múltiplos IDs (uso no cálculo de maturidade)."""
        ...
