from __future__ import annotations

from enum import Enum


class UserStatus(str, Enum):
    """Status de um usuário na plataforma."""

    PENDING = "PENDING"          # Aguardando ativação via e-mail
    ACTIVE = "ACTIVE"            # Ativo e pode fazer login
    INACTIVE = "INACTIVE"        # Desativado pelo admin


class CompanyStatus(str, Enum):
    """Status de uma empresa cadastrada."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class AssessmentStatus(str, Enum):
    """Status do ciclo de vida de uma avaliação."""

    IN_PROGRESS = "IN_PROGRESS"      # Avaliação iniciada, ainda editável
    FINALIZED = "FINALIZED"          # Concluída, resultados calculados, bloqueada
    CANCELLED = "CANCELLED"          # Cancelada antes de finalizar


class InvitationStatus(str, Enum):
    """Status de um convite de acesso enviado por e-mail."""

    PENDING = "PENDING"       # Aguardando aceite
    ACCEPTED = "ACCEPTED"     # Usuário ativou a conta via link
    REVOKED = "REVOKED"       # Convite revogado pelo admin
    EXPIRED = "EXPIRED"       # Token expirado


class ReportJobStatus(str, Enum):
    """Status de um job de geração de relatório (PDF / IA)."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class AnswerType(str, Enum):
    """Tipo da resposta para uma pergunta do questionário."""

    SCORED = "SCORED"          # Resposta com pontuação numérica (0-4)
    NOT_APPLICABLE = "NA"      # Não se aplica – exige justificativa, excluída do cálculo
    NOT_KNOWN = "NS"           # Não sabe – reduz cobertura, não recebe nota


class EvidenceType(str, Enum):
    """Tipo de evidência anexada a uma resposta."""

    FILE = "FILE"              # Arquivo enviado (upload)
    LINK = "LINK"              # URL/link externo


class EvidenceStatus(str, Enum):
    """Status de processamento de uma evidência."""

    ACTIVE = "ACTIVE"
    DELETED = "DELETED"


class DiagnosticSufficiency(str, Enum):
    """Suficiência do preenchimento para geração de diagnóstico."""

    READY_FOR_REVIEW = "READY_FOR_REVIEW"       # Cobertura >= 80% e todas as dimensões com notas
    PRELIMINARY = "PRELIMINARY"                 # Cobertura < 80% ou alguma dimensão sem notas
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"     # Nenhuma resposta numérica registrada


class RecommendationPriority(str, Enum):
    """Prioridade de uma recomendação no relatório gerado por IA."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class UserRole(str, Enum):
    """Papel/perfil de um usuário dentro da plataforma."""

    ADMIN = "ADMIN"           # Administrador da plataforma (Prisma TI)
    IT_RESPONSIBLE = "IT_RESPONSIBLE"  # Acesso consultivo
    MANAGER = "MANAGER"       # Gestor de TI de uma empresa cliente
