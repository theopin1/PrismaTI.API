from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class AlternativeDTO:
    """DTO de alternativa de resposta."""

    id: uuid.UUID
    pergunta_id: uuid.UUID
    descricao: str
    pontuacao: int
    ordem: int


@dataclass
class QuestionDTO:
    """DTO de pergunta com alternativas."""

    id: uuid.UUID
    dimensao_id: uuid.UUID
    texto: str
    ordem: int
    codigo: str
    explicacao: str
    orientacao_evidencia: str
    alternativas: list[AlternativeDTO] = field(default_factory=list)


@dataclass
class DimensionDTO:
    """DTO de dimensão com perguntas."""

    id: uuid.UUID
    versao_questionario_id: uuid.UUID
    nome: str
    descricao: str
    ordem: int
    codigo: str
    perguntas: list[QuestionDTO] = field(default_factory=list)


@dataclass
class CreateQuestionnaireDTO:
    """Dados de entrada para criação de questionário."""

    nome: str
    descricao: str


@dataclass
class QuestionnaireVersionOutputDTO:
    """Dados de saída de uma versão de questionário."""

    id: uuid.UUID
    questionario_id: uuid.UUID
    questionario_nome: str
    versao: str
    versao_metodologia: str
    status: str
    publicado_em: datetime | None
    dimensoes: list[DimensionDTO] = field(default_factory=list)
