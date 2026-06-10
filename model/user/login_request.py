from pydantic import BaseModel


class LoginRequest(BaseModel):
    cpf : str
    password : str
