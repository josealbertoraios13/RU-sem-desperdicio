from pydantic import BaseModel


class SchedulesRequest(BaseModel):
    user_cpf : str | None
