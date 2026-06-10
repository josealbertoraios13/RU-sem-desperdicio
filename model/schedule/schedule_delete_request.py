from pydantic import BaseModel


class ScheduleDeleteRequest(BaseModel):
    user_cpf : str
    schedule_type : str
    schedule_date : str
