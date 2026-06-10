
from fastapi import APIRouter, Query

from model import Schedule, ScheduleDeleteRequest, ScheduleRequest, ScheduleUpdateRequest
from services import ScheduleService

router = APIRouter()
schedule_service = ScheduleService()

@router.post("/schedule/register")
def schedule_register(request : ScheduleRequest) -> dict:
    schedule = Schedule(
        user_cpf=request.user_cpf,
        schedule_type=request.schedule_type,
        schedule_date=request.schedule_date,
        estimated_time=request.estimated_time,
        meal_type=request.meal_type
    )

    return schedule_service.schedule_register(schedule=schedule)

@router.put("/schedule/update")
def schedule_update(request : ScheduleUpdateRequest) -> dict:
    return schedule_service.schedule_update(
        user_cpf=request.user_cpf,
        schedule_type=request.schedule_type,
        schedule_date=request.schedule_date,
        estimated_time=request.estimated_time,
        id=request.id,
        meal_type=request.meal_type)

@router.delete("/schedule/delete")
def schedule_delete(request : ScheduleDeleteRequest) -> dict:
    return schedule_service.schedule_delete(
        user_cpf=request.user_cpf,
        schedule_type=request.schedule_type,
        schedule_date=request.schedule_date
    )

@router.get("/schedule/all")
def get_schedules(user_cpf : str | None = Query(None), date : str | None = Query(None)) -> dict:
    return schedule_service.get_schedules(cpf=user_cpf, date=date)
