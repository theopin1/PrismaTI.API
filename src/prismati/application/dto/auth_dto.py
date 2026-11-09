from __future__ import annotations

from dataclasses import dataclass

from prismati.domain.enums.status import UserRole


@dataclass
class LoginInputDTO:
    """Dados de entrada para autenticação."""

    email: str
    senha: str


@dataclass
class LoginOutputDTO:
    """Token de acesso retornado após autenticação bem-sucedida."""

    access_token: str
    token_type: str
    usuario_id: str
    nome: str
    email: str
    role: UserRole


@dataclass
class ActivateAccountDTO:
    """Dados para ativar conta via link de convite."""

    token: str
    nome: str
    senha: str


@dataclass
class ForgotPasswordDTO:
    """Dados de entrada para solicitar redefinição de senha."""

    email: str


@dataclass
class ResetPasswordDTO:
    """Dados para confirmar redefinição de senha via token."""

    token: str
    nova_senha: str
