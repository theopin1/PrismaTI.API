from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime

from prismati.domain.enums.status import DiagnosticSufficiency


@dataclass
class DimensionResult:
    """Resultado calculado de maturidade para uma dimensão específica."""

    dimensao_id: uuid.UUID
    dimensao_nome: str
    dimensao_codigo: str
    total_perguntas: int
    respostas_numericas: int       # respostas com pontuação (SCORED)
    respostas_na: int              # respostas Não Aplicável
    respostas_ns: int              # respostas Não Sabe
    soma_notas: float              # soma das pontuações numéricas
    # None quando não há respostas numéricas para a dimensão
    maturidade: float | None = None
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    avaliacao_resultado_id: uuid.UUID | None = None


@dataclass
class AssessmentResult:
    """Resultado consolidado de uma avaliação de maturidade."""

    avaliacao_id: uuid.UUID
    total_perguntas: int
    perguntas_preenchidas: int
    respostas_numericas: int
    maturidade_geral: float | None      # None se nenhuma dimensão com resultado
    cobertura: float                     # respostas_numericas / (total - NA justificadas) * 100
    preenchimento: float                 # preenchidas / total * 100
    suficiencia: DiagnosticSufficiency
    dimensoes: list[DimensionResult] = field(default_factory=list)
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    calculado_em: datetime = field(default_factory=datetime.utcnow)
