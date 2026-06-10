import datetime

# --- Constantes de Regras de Negócio ---
FERIADOS_FIXOS = {
        (1, 1),   # Ano Novo
        (4, 21),  # Tiradentes
        (5, 1),   # Dia do Trabalho
        (9, 7),   # Independência
        (10, 12), # Nossa Senhora Aparecida
        (11, 2),  # Finados
        (11, 15), # Proclamação da República
        (12, 25), # Natal
    }

ALMOCO_ABERTURA   = (10, 30)
ALMOCO_FECHAMENTO = (14,  0)
JANTAR_ABERTURA   = (17, 00)
JANTAR_FECHAMENTO = (20,  0)

SEMESTRE_1 = ((3, 1), (8, 31))
SEMESTRE_2 = ((9, 1), (2, 28))

MEAL_TYPE_ALIASES = {
    "select": "select",
    "leve sabor": "leve_sabor",
    "leve_sabor": "leve_sabor",
    "leve-sabor": "leve_sabor",
    "essencial": "essencial",
}

class ScheduleUtils:
    error : str = "null"
    """
    ============================FOR_TIME==================================
    """
    @staticmethod
    def _in_interval(current_date : datetime.date, start, end):
        month_day = (current_date.month, current_date.day)

        return start <= month_day <= end if start <= end else (month_day >= start or month_day <= end)

    @staticmethod
    def _format_time_tuple(h: int, m: int) -> str:
        # Formata inteiros de horas e minutos para a string HH:MM.
        return f"{h:02d}:{m:02d}"
    """
    =============================SCHEDULE_TPE==============================
    """
    @staticmethod
    def _is_valid_schedule_type(schedule_type : str) -> bool:
        return schedule_type == "lunch" or schedule_type == "dinner"

    @staticmethod
    def validate_schedule_type(schedule_type : str) -> None:
        if not ScheduleUtils._is_valid_schedule_type(schedule_type=schedule_type):
            ScheduleUtils.return_http_exception()

    """
    =============================MEAL_TYPE==============================
    """
    @staticmethod
    def normalize_meal_type(meal_type: str) -> str:
        if not meal_type or not isinstance(meal_type, str):
            ScheduleUtils.error = "Tipo de refeicao invalido"
            ScheduleUtils.return_http_exception()

        normalized = meal_type.strip().lower()
        canonical_meal_type = MEAL_TYPE_ALIASES.get(normalized)

        if not canonical_meal_type:
            ScheduleUtils.error = "Tipo de refeicao invalido"
            ScheduleUtils.return_http_exception()

        return canonical_meal_type
    """
    ===================================DATE======================================
    """
    @staticmethod
    def _is_valid_date(text: str) -> bool:
        try:
            day, month, year = text.split("/")
            schedule_date = datetime.date(int(year), int(month), int(day))
        except (ValueError, AttributeError):
            ScheduleUtils.error = "Data inválida. Use DD/MM/AAAA"
            return False

        today = datetime.date.today()

        is_sched_s1 = ScheduleUtils._in_interval(schedule_date, *SEMESTRE_1)
        is_today_s1 = ScheduleUtils._in_interval(today, *SEMESTRE_1)

        if is_sched_s1 != is_today_s1:
            ScheduleUtils.error = "A data marcada não pode estar fora do semestre atual"
            return False

        if schedule_date < today:
            ScheduleUtils.error = "A data não pode estar no passado"
            return False

        if schedule_date.weekday() in (5, 6):
            ScheduleUtils.error = "O restaurante não funciona aos fins de semana"
            return False

        if (schedule_date.month, schedule_date.day) in FERIADOS_FIXOS:
            ScheduleUtils.error = "Esta data é um feriado nacional"
            return False

        return True

    @staticmethod
    def validate_date(date: str) -> None:
        if not date or not isinstance(date, str):
            ScheduleUtils.error = "Data inválida. Use DD/MM/AAAA"
            ScheduleUtils.return_http_exception()
        if not ScheduleUtils._is_valid_date(date):
            ScheduleUtils.return_http_exception()
    """
    ======================================FOR_TIME======================================
    """
    @staticmethod
    def _is_valid_time(time_str: str, opening: tuple, closing: tuple) -> bool:
        if len(time_str) != 5 or ":" not in time_str:
            ScheduleUtils.error = "Formato incompleto ou inválido. Use HH:MM"
            return False

        try:
            h, m = map(int, time_str.split(":"))
        except ValueError:
            ScheduleUtils.error = "Horário inválido"
            return False

        if not (0 <= h <= 23 and 0 <= m <= 59):
            ScheduleUtils.error = "Horário inválido"
            return False

        time_mins = h * 60 + m
        open_mins = opening[0] * 60 + opening[1]
        close_mins = closing[0] * 60 + closing[1]

        if not (open_mins <= time_mins <= close_mins):
            opening_str = ScheduleUtils._format_time_tuple(*opening)
            closing_str = ScheduleUtils._format_time_tuple(*closing)

            ScheduleUtils.error = f"Fora do horário permitido ({opening_str} às {closing_str})"
            return False

        return True

    @staticmethod
    def validate_time(schedule_type : str, estimated_time : str) -> None:
        if schedule_type == "lunch":
            if not ScheduleUtils._is_valid_time(
                time_str=estimated_time,
                opening=ALMOCO_ABERTURA, closing=ALMOCO_FECHAMENTO
            ):
                ScheduleUtils.return_http_exception()

        elif schedule_type == "dinner" and not ScheduleUtils._is_valid_time(
            time_str=estimated_time,
            opening=JANTAR_ABERTURA, closing=JANTAR_FECHAMENTO
        ):
            ScheduleUtils.return_http_exception()


    @staticmethod
    def return_http_exception() -> None:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail={"msg" : ScheduleUtils.error})
