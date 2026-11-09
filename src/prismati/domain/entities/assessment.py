from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime

from prismati.domain.enums.status import AssessmentStatus
from prismati.domain.exceptions.domain_exceptions import BusinessRuleError


@dataclass
class Assessment:
    """Entidade de domínio que representa uma avaliação de maturidade de TI de uma empresa."""

    empresa_id: uuid.UUID
    gestor_usuario_id: uuid.UUID
    versao_questionario_id: uuid.UUID
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    status: AssessmentStatus = AssessmentStatus.IN_PROGRESS
    iniciada_em: datetime = field(default_factory=datetime.utcnow)
    finalizada_em: datetime | None = None

    @property
    def is_in_progress(self) -> bool:
        return self.status == AssessmentStatus.IN_PROGRESS

    @property
    def is_finalized(self) -> bool:
        return self.status == AssessmentStatus.FINALIZED

    def finalize(self) -> None:
        """Finaliza a avaliação calculando resultados e bloqueando edição."""
        if self.status != AssessmentStatus.IN_PROGRESS:
            raise BusinessRuleError(
                f"Apenas avaliações em andamento podem ser finalizadas. Status atual: '{self.status}'."
            )
        self.status = AssessmentStatus.FINALIZED
        self.finalizada_em = datetime.utcnow()

    def cancel(self) -> None:
        """Cancela a avaliação."""
        if self.status == AssessmentStatus.FINALIZED:
            raise BusinessRuleError("Uma avaliação já finalizada não pode ser cancelada.")
        self.status = AssessmentStatus.CANCELLED

    def assert_editable(self) -> None:
        """Lança exceção se a avaliação não estiver em andamento (edição bloqueada)."""
        if not self.is_in_progress:
            raise BusinessRuleError(
                "Esta avaliação não está mais em andamento e não pode ser editada."
            )
