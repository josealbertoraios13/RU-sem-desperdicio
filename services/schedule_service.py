from datetime import date

from fastapi import HTTPException

from smartru.model import Schedule
from smartru.repository import ScheduleRepository, UserRepository
from smartru.services.service import Service
from smartru.utils import ReportUtils, ScheduleUtils, UserUtils


class ScheduleService(Service):
    def __init__(self) -> None:
        self.schedule_repository = ScheduleRepository()
        self.user_repository = UserRepository()

    def schedule_register(self, schedule : Schedule) -> dict:
        tmp_cpf = UserUtils.validate_cpf(cpf=schedule.user_cpf)

        ScheduleUtils.validate_schedule_type(schedule_type=schedule.schedule_type)

        ScheduleUtils.validate_date(schedule.schedule_date)
        meal_type = ScheduleUtils.normalize_meal_type(schedule.meal_type)

        parsed_date = ReportUtils.parse_date(schedule.schedule_date, "%d/%m/%Y")

        ScheduleUtils.validate_time(schedule_type=schedule.schedule_type, estimated_time=schedule.estimated_time)

        result = self.schedule_repository.schedule_register(
            user_cpf=tmp_cpf,
            schedule_type=schedule.schedule_type,
            schedule_date=parsed_date,
            estimated_time=schedule.estimated_time,
            meal_type=meal_type,
        )

        return self.handle_response(response=result)

    def schedule_update(
        self,
        user_cpf : str,
        schedule_type : str,
        schedule_date : str,
        estimated_time : str,
        id : int,
        meal_type: str,
    ) -> dict:
        tmp_cpf = UserUtils.validate_cpf(cpf=user_cpf)

        ScheduleUtils.validate_schedule_type(schedule_type=schedule_type)
        normalized_meal_type = ScheduleUtils.normalize_meal_type(meal_type)

        ScheduleUtils.validate_time(schedule_type=schedule_type, estimated_time=estimated_time)

        ScheduleUtils.validate_date(schedule_date)

        parsed_date = ReportUtils.parse_date(schedule_date, "%d/%m/%Y")

        result = self.schedule_repository.schedule_update(
            user_cpf=tmp_cpf,
            schedule_type=schedule_type,
            schedule_date=parsed_date,
            estimated_time=estimated_time,
            id=id,
            meal_type=normalized_meal_type,
        )

        return self.handle_response(response=result)

    def schedule_delete(self, user_cpf : str, schedule_type : str, schedule_date : str) -> dict:
        tmp_cpf = UserUtils.validate_cpf(cpf=user_cpf)

        ScheduleUtils.validate_schedule_type(schedule_type=schedule_type)
        ScheduleUtils.validate_date(date=schedule_date)

        parsed_date = ReportUtils.parse_date(date=schedule_date, format="%d/%m/%Y")

        result = self.schedule_repository.schedule_delete(user_cpf=tmp_cpf, schedule_type=schedule_type, schedule_date=parsed_date)
        return self.handle_response(result)

    def get_schedules(self, cpf : str | None, date : str | None) -> dict:

        parsed_date = None

        if date:
            ReportUtils.validate_date(date=date)

            parsed_date = ReportUtils.parse_date(date=date, format="%d/%m/%Y")

        tmp_cpf = None
        if cpf:
            tmp_cpf = UserUtils.validate_cpf(cpf=cpf)

        result = self.schedule_repository.get_all_schedules(user_cpf=tmp_cpf, schedule_date=parsed_date)

        return self.handle_response(response=result)

    def confirm_consumption(self, schedule_id: int, employee_cpf: str) -> dict:
        tmp_cpf = UserUtils.validate_cpf(employee_cpf)

        employee = self.user_repository.get_user_by_cpf(tmp_cpf)
        employee = self.handle_response(response=employee)

        schedule_result = self.schedule_repository.get_schedule_by_id(schedule_id)
        schedule_result = self.handle_response(response=schedule_result)

        schedule = schedule_result["data"]
        schedule_date = schedule["schedule_date"]

        if isinstance(schedule_date, str):
            from datetime import datetime
            schedule_date = datetime.strptime(schedule_date, "%Y-%m-%d").date()

        if schedule_date != date.today():
            raise HTTPException(
                status_code=400,
                detail={"msg": "Confirmação permitida apenas no dia da refeição"}
            )

        if schedule["status"] == "CONFIRMADO":
            raise HTTPException(
                status_code=409,
                detail={"msg": "Consumo já confirmado para este agendamento"}
            )

        if schedule["status"] == "CANCELADO":
            raise HTTPException(
                status_code=400,
                detail={"msg": "Não é possível confirmar consumo de agendamento cancelado"}
            )

        result = self.schedule_repository.confirm_consumption(schedule_id=schedule_id, employee_id=employee["id"])

        return self.handle_response(response=result)

    def get_consumption_report(self, start_date: str, end_date: str | None = None) -> dict:
        ReportUtils.validate_date(date=start_date)

        parsed_start = ReportUtils.parse_date(date=start_date, format="%d/%m/%Y")

        parsed_end = None
        if end_date:
            ReportUtils.validate_date(date=end_date)
            parsed_end = ReportUtils.parse_date(date=end_date, format="%d/%m/%Y")

        result = self.schedule_repository.get_consumption_report(start_date=parsed_start, end_date=parsed_end)

        return self.handle_response(response=result)

    def get_daily_summary(self, target_date: str) -> dict:
        ReportUtils.validate_date(date=target_date)

        parsed_date = ReportUtils.parse_date(date=target_date, format="%d/%m/%Y")

        result = self.schedule_repository.get_daily_summary(target_date=parsed_date)

        return self.handle_response(response=result)
