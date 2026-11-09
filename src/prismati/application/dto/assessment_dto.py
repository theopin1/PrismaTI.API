from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime

from prismati.domain.enums.status import AssessmentStatus, AnswerType


@dataclass
class StartAssessmentDTO:
    """Dados de entrada para iniciar uma avaliação."""

    empresa_id: uuid.UUID
    versao_questionario_id: uuid.UUID
    gestor_usuario_id: uuid.UUID


@dataclass
class AssessmentOutputDTO:
    """Dados de saída de uma avaliação."""

    id: uuid.UUID
    empresa_id: uuid.UUID
    gestor_usuario_id: uuid.UUID
    versao_questionario_id: uuid.UUID
    status: AssessmentStatus
    iniciada_em: datetime
    finalizada_em: datetime | None


@dataclass
class AnswerInputDTO:
    """Dados de entrada para salvar ou atualizar uma resposta."""

    avaliacao_id: uuid.UUID
    pergunta_id: uuid.UUID
    tipo_resposta: AnswerType
    usuario_id: uuid.UUID            # usuário que está salvando (deve ser o gestor responsável)
    alternativa_id: uuid.UUID | None = None
    justificativa: str | None = None


@dataclass
class AnswerOutputDTO:
    """Dados de saída de uma resposta."""

    id: uuid.UUID
    avaliacao_id: uuid.UUID
    pergunta_id: uuid.UUID
    tipo_resposta: AnswerType
    alternativa_id: uuid.UUID | None
    justificativa: str | None
    atualizado_em: datetime
    pontuacao: int | None = None          # pontuação da alternativa selecionada, se SCORED
    pontuacao_percentual: float | None = None  # (pontuacao / 4) * 100


@dataclass
class AssessmentProgressDTO:
    """Dados de progresso de preenchimento de uma avaliação."""

    avaliacao_id: uuid.UUID
    total_perguntas: int
    perguntas_respondidas: int
    perguntas_na: int
    perguntas_ns: int
    percentual_preenchimento: float
    dimensoes: list[dict] = field(default_factory=list)
