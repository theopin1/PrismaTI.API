from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime

from prismati.domain.enums.status import DiagnosticSufficiency


@dataclass
class DimensionResultDTO:
    """DTO com resultado de maturidade de uma dimensão."""

    dimensao_id: uuid.UUID
    dimensao_nome: str
    dimensao_codigo: str
    total_perguntas: int
    respostas_numericas: int
    respostas_na: int
    respostas_ns: int
    soma_notas: float
    maturidade: float | None   # None = sem dados suficientes nesta dimensão


@dataclass
class AssessmentResultDTO:
    """DTO com resultado consolidado de uma avaliação."""

    avaliacao_id: uuid.UUID
    total_perguntas: int
    perguntas_preenchidas: int
    respostas_numericas: int
    maturidade_geral: float | None
    cobertura: float
    preenchimento: float
    suficiencia: DiagnosticSufficiency
    calculado_em: datetime
    dimensoes: list[DimensionResultDTO] = field(default_factory=list)
