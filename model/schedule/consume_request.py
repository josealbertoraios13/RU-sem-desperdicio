from pydantic import BaseModel


class ConsumeRequest(BaseModel):
    schedule_id: int
    employee_cpf: str
