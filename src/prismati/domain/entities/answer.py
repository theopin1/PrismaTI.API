from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime

from prismati.domain.enums.status import AnswerType
from prismati.domain.exceptions.domain_exceptions import ValidationError


@dataclass
class Answer:
    """Entidade de domínio que representa a resposta de uma pergunta em uma avaliação.

    Regras:
    - tipo_resposta == NA → justificativa obrigatória, excluída do cálculo de maturidade.
    - tipo_resposta == NS → reduz cobertura, não recebe nota numérica.
    - tipo_resposta == SCORED → alternativa_id obrigatória com pontuação 0-4.
    """

    avaliacao_id: uuid.UUID
    pergunta_id: uuid.UUID
    versao_questionario_id: uuid.UUID
    tipo_resposta: AnswerType
    atualizado_por: uuid.UUID
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    alternativa_id: uuid.UUID | None = None
    justificativa: str | None = None
    atualizado_em: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        if self.tipo_resposta == AnswerType.NOT_APPLICABLE and not self.justificativa:
            raise ValidationError(
                "Justificativa é obrigatória para respostas 'Não Aplicável'.",
                field="justificativa",
            )
        if self.tipo_resposta == AnswerType.SCORED and self.alternativa_id is None:
            raise ValidationError(
                "Alternativa é obrigatória para respostas com pontuação.",
                field="alternativa_id",
            )

    def update(
        self,
        tipo_resposta: AnswerType,
        atualizado_por: uuid.UUID,
        alternativa_id: uuid.UUID | None = None,
        justificativa: str | None = None,
    ) -> None:
        """Atualiza os dados da resposta (somente se a avaliação ainda estiver em andamento)."""
        self.tipo_resposta = tipo_resposta
        self.alternativa_id = alternativa_id
        self.justificativa = justificativa
        self.atualizado_por = atualizado_por
        self.atualizado_em = datetime.utcnow()
        self._validate()

    @property
    def is_scored(self) -> bool:
        return self.tipo_resposta == AnswerType.SCORED

    @property
    def is_not_applicable(self) -> bool:
        return self.tipo_resposta == AnswerType.NOT_APPLICABLE

    @property
    def is_not_known(self) -> bool:
        return self.tipo_resposta == AnswerType.NOT_KNOWN
