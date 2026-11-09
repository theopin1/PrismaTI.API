from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime

from prismati.domain.enums.status import ReportJobStatus, RecommendationPriority


@dataclass
class ReportJobOutputDTO:
    """DTO com dados de um job de geração de relatório."""

    id: uuid.UUID
    avaliacao_id: uuid.UUID
    status: ReportJobStatus
    solicitado_em: datetime
    concluido_em: datetime | None
    download_url: str | None = None   # URL para download quando COMPLETED
    erro: str | None = None           # Mensagem de erro quando FAILED


@dataclass
class AIRecommendationDTO:
    """DTO com uma recomendação gerada por IA."""

    dimensao_codigo: str
    dimensao_nome: str
    prioridade: RecommendationPriority
    titulo: str
    descricao: str
    acoes_sugeridas: list[str] = field(default_factory=list)


@dataclass
class AIReportOutputDTO:
    """DTO com o relatório gerado por IA (diagnóstico + recomendações)."""

    id: uuid.UUID
    avaliacao_id: uuid.UUID
    sumario_executivo: str
    pontos_fortes: list[str]
    pontos_melhoria: list[str]
    recomendacoes: list[AIRecommendationDTO]
    gerado_em: datetime
    versao_modelo_ia: str = ""
