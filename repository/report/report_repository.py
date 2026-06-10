from repository.repository import Repository
from utils import logger

SCHEDULE_DEMAND_KEYS = ("lunch", "dinner")
MEAL_DEMAND_KEYS = ("select", "leve_sabor", "essencial")


class ReportRepository(Repository):

    def get_demand(self, schedule_date) -> dict:
        try:
            with self.get_connect() as conn:
                with conn.cursor() as cursor:
                    sql_query = """
                        SELECT schedule_type, meal_type, COUNT(*)
                        FROM schedules
                        WHERE schedule_date = %s
                        GROUP BY schedule_type, meal_type
                    """

                    cursor.execute(sql_query, (schedule_date,))

                    result = cursor.fetchall()

                    data = self._build_empty_demand_data()
                    self._apply_demand_counts(data=data, rows=result)

                    return self.build_response(
                        router="get_demand", msg="Dados resgatados com sucesso!",
                        data=data
                    )

        except Exception as exception:
            logger.error(f"Error in get_demand: {exception}")

            return self.build_response(
                router="get_demand", msg=f"Erro inesperado: {exception}",
                success=False, code=500
            )

    @staticmethod
    def _build_empty_demand_data() -> dict:
        return {key: 0 for key in (*SCHEDULE_DEMAND_KEYS, *MEAL_DEMAND_KEYS)}

    @staticmethod
    def _apply_demand_counts(data: dict, rows: list[tuple]) -> None:
        for schedule_type, meal_type, count in rows:
            if schedule_type in SCHEDULE_DEMAND_KEYS:
                data[schedule_type] += count

            if meal_type in MEAL_DEMAND_KEYS:
                data[meal_type] += count

    def get_export_data(self, schedule_date):
        try:
            with self.get_connect() as conn, conn.cursor() as cursor:
                sql_query = """
                        SELECT u.name, s.user_cpf, s.schedule_type,
                        s.schedule_date AS data, s.estimated_time, s.created_at
                        FROM schedules s
                        JOIN users u ON u.cpf = s.user_cpf
                        WHERE s.schedule_date = %s
                    """

                cursor.execute(sql_query, (schedule_date,))

                columns = [desc[0] for desc in cursor.description]
                data = [dict(zip(columns, row)) for row in cursor.fetchall()]

                return self.build_response(
                    router="get_export_data", msg="dados resgatados com sucesso!",
                    data=data
                )

        except Exception as exception:
            logger.error(f"Error in get_export_data: {exception}")
            return self.build_response(
                router="get_export_data", msg=f"Erro inesperado: {exception}",
                success=False, code=500
            )
