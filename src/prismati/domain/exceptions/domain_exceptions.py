from __future__ import annotations


class DomainException(Exception):
    """Base para todas as exceções de domínio da aplicação."""

    default_message: str = "Ocorreu um erro de domínio."

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.default_message
        super().__init__(self.message)


class NotFoundError(DomainException):
    """Recurso solicitado não foi encontrado."""

    default_message = "Recurso não encontrado."

    def __init__(self, resource: str = "Recurso", identifier: str | int | None = None) -> None:
        if identifier is not None:
            msg = f"{resource} com identificador '{identifier}' não foi encontrado."
        else:
            msg = f"{resource} não foi encontrado."
        super().__init__(msg)


class ConflictError(DomainException):
    """Operação conflita com o estado atual do recurso."""

    default_message = "Conflito com o estado atual do recurso."

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.default_message)


class ForbiddenError(DomainException):
    """Operação não permitida para o usuário atual."""

    default_message = "Acesso negado. Você não tem permissão para realizar esta operação."

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.default_message)


class ValidationError(DomainException):
    """Dados de entrada inválidos."""

    default_message = "Dados inválidos."

    def __init__(self, message: str | None = None, field: str | None = None) -> None:
        if field:
            msg = f"Campo '{field}': {message or self.default_message}"
        else:
            msg = message or self.default_message
        super().__init__(msg)
        self.field = field


class BusinessRuleError(DomainException):
    """Violação de regra de negócio."""

    default_message = "Regra de negócio violada."

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.default_message)
