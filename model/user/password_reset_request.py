"""
Este modelo de objeto serve para manipular/ler e transportar os dados
de recuperação de senha dentro da API
"""
from pydantic import BaseModel, EmailStr


class PasswordRecoverRequest(BaseModel):
    """Request model for initiating password recovery."""
    cpf: str
    email: EmailStr


class PasswordResetRequest(BaseModel):
    """Request model for resetting password with token."""
    token: str
    new_password: str


class PasswordResetToken(BaseModel):
    """Model for password reset token data."""
    id: int
    user_cpf: str
    token_hash: str
    created_at: str
    expires_at: str
    used: bool
