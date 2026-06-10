
from fastapi import APIRouter, Query

from smartru.model import ConsumeRequest
from smartru.services import ScheduleService

router = APIRouter()
schedule_service = ScheduleService()

@router.post("/schedule/consume")
def confirm_consumption(consume_request: ConsumeRequest) -> dict:
    return schedule_service.confirm_consumption(
        schedule_id=consume_request.schedule_id,
        employee_cpf=consume_request.employee_cpf
    )

@router.get("/report/daily-summary")
def daily_summary(date: str = Query(...)) -> dict:
    return schedule_service.get_daily_summary(target_date=date)

@router.get("/report/consumption")
def consumption_report(start_date: str = Query(...), end_date: str | None = Query(None)) -> dict:
    return schedule_service.get_consumption_report(start_date=start_date, end_date=end_date)
