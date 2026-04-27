from datetime import datetime, date

class MenuHistoryUtils:
    @staticmethod
    def sort_schedules(schedules: list) -> list:
        # Filtra pelo user_id, separa válidos de expirados e ordena:
        # - Válidos: do mais próximo ao mais distante (datetime asc)
        # - Expirados: do mais recente ao mais antigo (datetime desc)

        now = datetime.now()

        valid   = []
        expired = []

        for item in schedules:
            dt = MenuHistoryUtils.earliest_datetime(item)
            if dt is None:
                expired.append((datetime.min, item))
                continue

            if dt < now:
                expired.append((dt, item))
            else:
                valid.append((dt, item))

        valid.sort(key=lambda t: t[0])
        expired.sort(key=lambda t: t[0], reverse=True)

        return [item for _, item in valid] + [item for _, item in expired]

    @staticmethod
    def earliest_datetime(item: dict) -> datetime | None:
        #Retorna o datetime do horário do agendamento, ou None se nenhum horário estiver preenchido.

        date_str = item.get("data", "")
        try:
            day, month, year = date_str.split("/")
            base = date(int(year), int(month), int(day))
        except (ValueError, AttributeError):
            return None

        candidates = []
        t_str = item.get("horario")
        if t_str:
            try:
                hh, mm = t_str.split(":")
                candidates.append(
                    datetime(base.year, base.month, base.day, int(hh), int(mm))
                )
            except (ValueError, AttributeError):
                pass

        if not candidates:
            # Sem horário: usa meia-noite do dia
            return datetime(base.year, base.month, base.day, 0, 0)

        return min(candidates)
    
    @staticmethod
    def is_expired(item: dict, now: datetime) -> bool:
        # Retorna True se o horário do agendamento já passou.

        date_str = item.get("data", "")
        try:
            day, month, year = date_str.split("/")
            base = date(int(year), int(month), int(day))
        except (ValueError, AttributeError):
            return True

        # Procura pelo campo horario (formato HH:MM)
        horario_str = item.get("horario")
        if not horario_str:
            # Se não tem horário, compara apenas pela data
            return datetime(base.year, base.month, base.day) < now
        
        try:
            hh, mm = horario_str.split(":")
            schedule_datetime = datetime(
                base.year, base.month, base.day, int(hh), int(mm))
            return schedule_datetime < now
        except (ValueError, AttributeError):
            return True

    @staticmethod
    def format_label(item: dict, expired: bool, x_max: int) -> str:
        # Formata a linha do botão:
        #  [EXPIRADO]  DD/MM/AAAA  Almoço 11:30  Jantar 18:30
        # ou
        #              DD/MM/AAAA  Almoço 11:30  Jantar 18:30

        parts = []

        if expired:
            parts.append("[EXPIRADO]")

        data = item.get("data", "??/??/????")
        parts.append(data)

        refeicao = "almoco" if item.get("refeicao") == "almoco" else "jantar"
        horario = item.get("horario", "")
        parts.append(f"{refeicao} Horário estimado: {horario}".strip())

        label = "  ".join(parts)
        max_w = x_max - 8
        if len(label) > max_w:
            label = label[:max_w - 1] + "…"
        return label
