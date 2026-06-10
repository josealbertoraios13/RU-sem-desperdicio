from pydantic import BaseModel


class UpdatePasswordRequest(BaseModel):
    cpf : str
    current_password : str
    new_password : str
