"""
Request model for initiating password recovery.
This model is deprecated in favor of the one in password_reset_request.py
Kept for backward compatibility.
"""
from pydantic import BaseModel


class PasswordRecoverRequest(BaseModel):
    cpf: str
    email: str
