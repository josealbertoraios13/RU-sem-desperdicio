from pydantic import BaseModel


class ScheduleUpdateRequest(BaseModel):
    id : int
    user_cpf : str
    schedule_type : str
    schedule_date : str
    estimated_time :str
    meal_type : str
