from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime

from prismati.domain.enums.status import CompanyStatus


@dataclass
class Company:
    """Entidade de domínio que representa uma empresa cliente da plataforma."""

    razao_social: str
    cnpj: str
    segmento: str
    porte: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    status: CompanyStatus = CompanyStatus.ACTIVE
    criado_em: datetime = field(default_factory=datetime.utcnow)

    def activate(self) -> None:
        """Ativa a empresa."""
        self.status = CompanyStatus.ACTIVE

    def deactivate(self) -> None:
        """Desativa a empresa."""
        self.status = CompanyStatus.INACTIVE

    def toggle_status(self) -> None:
        """Alterna entre ativo e inativo."""
        if self.status == CompanyStatus.ACTIVE:
            self.deactivate()
        else:
            self.activate()

    @property
    def is_active(self) -> bool:
        return self.status == CompanyStatus.ACTIVE

    def update(self, razao_social: str | None = None, segmento: str | None = None, porte: str | None = None) -> None:
        """Atualiza os dados editáveis da empresa."""
        if razao_social is not None:
            self.razao_social = razao_social
        if segmento is not None:
            self.segmento = segmento
        if porte is not None:
            self.porte = porte
