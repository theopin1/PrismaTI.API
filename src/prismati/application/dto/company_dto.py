from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from prismati.domain.enums.status import CompanyStatus


@dataclass
class CreateCompanyDTO:
    """Dados de entrada para criação de empresa (somente admin)."""

    razao_social: str
    cnpj: str
    segmento: str
    porte: str


@dataclass
class UpdateCompanyDTO:
    """Dados de entrada para atualização de empresa."""

    razao_social: str | None = None
    segmento: str | None = None
    porte: str | None = None


@dataclass
class CompanyOutputDTO:
    """Dados de saída de uma empresa para a camada de apresentação."""

    id: uuid.UUID
    razao_social: str
    cnpj: str
    segmento: str
    porte: str
    status: CompanyStatus
    criado_em: datetime
