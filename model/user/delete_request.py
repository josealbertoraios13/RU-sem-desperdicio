from pydantic import BaseModel


class DeleteRequest(BaseModel):
    cpf : str
