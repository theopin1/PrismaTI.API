from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from prismati.domain.exceptions.domain_exceptions import ValidationError


@dataclass
class Alternative:
    """Representa uma alternativa de resposta para uma pergunta (pontuação de 0 a 4)."""

    pergunta_id: uuid.UUID
    descricao: str
    pontuacao: int      # 0, 1, 2, 3 ou 4
    ordem: int
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    def __post_init__(self) -> None:
        if self.pontuacao not in range(5):
            raise ValidationError(f"Pontuação deve ser entre 0 e 4. Recebido: {self.pontuacao}", field="pontuacao")


@dataclass
class Question:
    """Entidade de domínio que representa uma pergunta do questionário."""

    dimensao_id: uuid.UUID
    texto: str
    ordem: int
    codigo: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    explicacao: str = ""
    orientacao_evidencia: str = ""
    alternativas: list[Alternative] = field(default_factory=list)

    def add_alternative(self, alternative: Alternative) -> None:
        """Adiciona uma alternativa à pergunta."""
        self.alternativas.append(alternative)

    def get_alternative(self, alternative_id: uuid.UUID) -> Alternative | None:
        """Retorna a alternativa pelo ID, ou None se não encontrada."""
        return next((a for a in self.alternativas if a.id == alternative_id), None)

    def validate_alternative_belongs(self, alternative_id: uuid.UUID) -> None:
        """Verifica se a alternativa pertence a esta pergunta."""
        if not self.get_alternative(alternative_id):
            raise ValidationError(
                f"Alternativa '{alternative_id}' não pertence à pergunta '{self.id}'.",
                field="alternativa_id",
            )
