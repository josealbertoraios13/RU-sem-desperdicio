"""
    Este modelo de objeto serve para manipular/ler e transportar os dados
    do agendamento dentro da API
"""

class Schedule:
    def __init__(
        self,
        user_cpf: str,
        schedule_type,
        schedule_date: str,
        estimated_time: str = "",
        meal_type: str = "",
    ) -> None:
        self.user_cpf = user_cpf
        self.schedule_type = schedule_type
        self.schedule_date = schedule_date
        self.estimated_time = estimated_time
        self.meal_type = meal_type
