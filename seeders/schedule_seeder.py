"""
Seed de schedules (agendamentos de refeições).

Cria schedules de exemplo para demonstração do sistema.
Pode ser executado independentemente dos outros seeds.
"""

from datetime import date, timedelta
from typing import Any

from smartru.seeders.base_seeder import BaseSeeder
from smartru.utils.logger import logger


class ScheduleSeeder(BaseSeeder):
    """Seeder para tabela de schedules."""

    seed_name = "schedule_seeder"
    required_fields = ["user_cpf", "schedule_type", "schedule_date", "meal_type"]

    # Janelas de tempo padrão
    LUNCH_TIME = "12:00"
    DINNER_TIME = "18:00"
    DEFAULT_MEAL_TYPE = "essencial"

    def __init__(self, connection_pool=None):
        super().__init__(connection_pool)

    def _get_existing_schedules(self, cpf: str, schedule_type: str, schedule_date: date) -> bool:
        """Verifica se schedule já existe."""
        return self._check_exists_composite(
            "schedules",
            ["user_cpf", "schedule_type", "schedule_date"],
            [cpf, schedule_type, schedule_date]
        )

    def _insert_schedule(
        self,
        user_cpf: str,
        schedule_type: str,
        schedule_date: date,
        estimated_time: str
    ) -> bool:
        """Insere um schedule."""
        query = """
            INSERT INTO schedules (user_cpf, schedule_type, schedule_date, estimated_time, meal_type)
            VALUES (%s, %s, %s, %s, %s)
        """
        params = (user_cpf, schedule_type, schedule_date, estimated_time, self.DEFAULT_MEAL_TYPE)
        try:
            self._execute_query(query, params)
            return True
        except Exception as e:
            logger.error(f"Erro ao inserir schedule {user_cpf}: {e}")
            return False

    def _get_sample_dates(self) -> list[date]:
        """Retorna datas de exemplo para seed (próximos 5 dias úteis)."""
        dates = []
        today = date.today()

        # Pega próximos 5 dias úteis a partir de hoje
        days_added = 0
        current_day = today

        while days_added < 5:
            # 0=segunda, 4=sexta, 5=sábado, 6=domingo
            if current_day.weekday() < 5:  # Segunda a Sexta
                dates.append(current_day)
                days_added += 1
            current_day += timedelta(days=1)

        return dates

    def seed(self, **kwargs) -> dict[str, Any]:
        """
        Executa seed de schedules.

        Cria schedules para:
        - Almoço (12:00)
        - Jantar (18:00)

        Returns:
            Dict com resumo da execução
        """
        self.reset_counts()
        logger.info("Iniciando seed de schedules...")

        # Busca todos os usuários existentes
        users_query = "SELECT cpf, role FROM users"
        users = self._execute_query(users_query, fetch=True)

        if not users:
            logger.warning("Nenhum usuário encontrado para criar schedules")
            return {
                "seed_name": self.seed_name,
                "success": True,
                "message": "Nenhum usuário encontrado",
                **self.get_summary()
            }

        sample_dates = self._get_sample_dates()
        logger.info(f"Criando schedules para {len(sample_dates)} dias")

        # Cria schedules para cada usuário
        for user in users:
            cpf = user["cpf"]

            for schedule_date in sample_dates:
                if not self._get_existing_schedules(cpf, "lunch", schedule_date):
                    if self._insert_schedule(cpf, "lunch", schedule_date, self.LUNCH_TIME):
                        self.inserted_count += 1
                    else:
                        self.error_count += 1
                else:
                    self.skipped_count += 1

                if not self._get_existing_schedules(cpf, "dinner", schedule_date):
                    if self._insert_schedule(cpf, "dinner", schedule_date, self.DINNER_TIME):
                        self.inserted_count += 1
                    else:
                        self.error_count += 1
                else:
                    self.skipped_count += 1

        summary = self.get_summary()
        logger.info(
            f"Seed de schedules finalizado: "
            f"{summary['inserted']} inseridos, "
            f"{summary['skipped']} pulados, "
            f"{summary['errors']} erros"
        )

        return {
            "seed_name": self.seed_name,
            "success": True,
            **summary
        }
