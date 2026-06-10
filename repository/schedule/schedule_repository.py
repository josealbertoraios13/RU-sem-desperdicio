from datetime import date

from repository.repository import Repository
from utils import logger


class ScheduleRepository(Repository):
    PART = "schedule_repository"

    def schedule_register(
        self,
        user_cpf: str,
        schedule_type: str,
        schedule_date,
        estimated_time: str,
        meal_type: str,
    ) -> dict:
        try:
            error_message = self._check_schedule_exists(user_cpf, schedule_type, schedule_date)
            if error_message:
                return self.build_response(
                    router="schedule_register", msg=error_message, success=False, code=409
                )

            with self.get_connect() as conn, conn.cursor() as cursor:
                sql_query = """INSERT INTO schedules
                    (user_cpf, schedule_type, schedule_date, estimated_time, meal_type)
                    VALUES (%s, %s, %s, %s, %s)"""

                cursor.execute(
                    sql_query,
                    (user_cpf, schedule_type, schedule_date, estimated_time, meal_type)
                )

                return self.build_response(
                    router="schedule_register",
                    msg=f"Sucesso: {schedule_type.capitalize()} agendado para {schedule_date}!"
                )

        except Exception as exception:
            logger.error(f"Error in schedule_register: {exception}")
            return self.build_response(
                router="schedule_register", msg=f"Erro inesperado: {exception}", success=False, code=500
            )

    def schedule_update(
        self,
        user_cpf: str,
        schedule_type: str,
        schedule_date : date,
        estimated_time: str,
        id: int,
        meal_type: str,
    ) -> dict:
        try:
            with self.get_connect() as conn:
                with conn.cursor() as cursor:
                    sql_query = """
                        UPDATE schedules
                        SET schedule_type = %s,
                            schedule_date = %s,
                            estimated_time = %s,
                            meal_type = %s
                        WHERE user_cpf = %s AND id = %s
                    """

                    cursor.execute(
                        sql_query,
                        (schedule_type, schedule_date, estimated_time, meal_type, user_cpf, id)
                    )

                    if cursor.rowcount == 0:
                        return self.build_response(
                            router="schedule_update",
                            msg="Agendamento não encontrado", success=False, code=404
                        )

                    return self.build_response(
                        router="schedule_update",
                        msg="Agendamento atualizado com sucesso"
                    )

        except Exception as exception:
            logger.error(f"Error in schedule_update: {exception}")
            return self.build_response(
                router="schedule_update", msg=f"Erro inesperado: {exception}", success=False, code=500
            )

    def schedule_delete(self, user_cpf: str, schedule_type: str, schedule_date : date) -> dict:
        try:
            with self.get_connect() as conn:
                with conn.cursor() as cursor:
                    sql_query = "DELETE FROM schedules WHERE user_cpf = %s AND schedule_type = %s AND schedule_date = %s"

                    cursor.execute(sql_query, (user_cpf, schedule_type, schedule_date))
                    deleted_count = cursor.rowcount

                    if deleted_count > 0:
                        return self.build_response(
                            router="schedule_delete",
                            msg=f"Sucesso: Agendamento de {schedule_type} para {schedule_date} excluído!"
                        )

                    return self.build_response(
                        router="schedule_delete",
                        msg="Erro: Nenhum agendamento encontrado com os critérios fornecidos", success=False, code=404
                    )

        except Exception as exception:
            logger.error(f"Error in schedule_delete: {exception}")
            return self.build_response(
                router="schedule_delete", msg=f"Erro inesperado: {exception}", success=False, code=500
            )

    def get_all_schedules(self, user_cpf=None, schedule_date=None) -> dict:
        try:
            with self.get_connect() as conn, conn.cursor() as cursor:
                sql_query = """
                        SELECT s.id, u.name, s.user_cpf,
                        s.schedule_type, s.meal_type, s.schedule_date,
                        s.estimated_time, s.status, s.created_at,
                        s.consumed_at, s.confirmed_by
                        FROM schedules s
                        JOIN users u ON u.cpf = s.user_cpf
                    """

                params = []
                conditions = []

                if user_cpf:
                    conditions.append("s.user_cpf = %s")
                    params.append(user_cpf)

                if schedule_date:
                    conditions.append("s.schedule_date = %s")
                    params.append(schedule_date)

                if conditions:
                    sql_query += " WHERE " + " AND ".join(conditions)

                sql_query += " ORDER BY s.schedule_date DESC, s.schedule_type"

                cursor.execute(sql_query, tuple(params))
                schedules = cursor.fetchall()

                if schedules:
                    columns = [desc[0] for desc in cursor.description]
                    data = [dict(zip(columns, row)) for row in schedules]

                    return self.build_response(
                        router="get_all_schedules",
                        msg="Agendamentos encontrados com sucesso", data=data
                    )

                return self.build_response(
                    router="get_all_schedules",
                    msg="Nenhum agendamento encontrado", success=False, code=404
                )

        except Exception as exception:
            logger.error(f"Error in get_all_schedules: {exception}")
            return self.build_response(
                router="get_all_schedules", msg=f"Erro inesperado: {exception}", success=False, code=500
            )

    def _check_schedule_exists(self, user_cpf: str, schedule_type: str, schedule_date) -> str | None:
        with self.get_connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM schedules WHERE user_cpf = %s AND schedule_type = %s AND schedule_date = %s",
                    (user_cpf, schedule_type, schedule_date)
                )
                if cursor.fetchone():
                    return "Agendamento duplicado"
        return None

    def get_schedule_by_id(self, schedule_id: int) -> dict:
        try:
            with self.get_connect() as conn, conn.cursor() as cursor:
                sql_query = """
                        SELECT s.id, u.name, s.user_cpf, s.schedule_type, s.meal_type,
                               s.schedule_date, s.estimated_time, s.status,
                               s.created_at, s.consumed_at, s.confirmed_by
                        FROM schedules s
                        JOIN users u ON u.cpf = s.user_cpf
                        WHERE s.id = %s
                    """
                cursor.execute(sql_query, (schedule_id,))
                result = cursor.fetchone()

                if not result:
                    return self.build_response(
                        router="get_schedule_by_id", msg="Agendamento não encontrado",
                        success=False, code=404
                    )

                columns = [desc[0] for desc in cursor.description]
                data = dict(zip(columns, result))

                return {"success": True, "data": data}
        except Exception as exception:
            logger.error(f"Error in get_schedule_by_id: {exception}")

            return self.build_response(
                router="get_schedule_by_id", msg=f"Erro inesperado: {exception}", success=False, code=500
            )

    def confirm_consumption(self, schedule_id: int, employee_id: int) -> dict:
        try:
            with self.get_connect() as conn:
                with conn.cursor() as cursor:
                    # Lock the row to prevent race conditions
                    cursor.execute(
                        "SELECT status FROM schedules WHERE id = %s FOR UPDATE",
                        (schedule_id,)
                    )
                    row = cursor.fetchone()

                    if not row:
                        return self.build_response(
                            router="confirm_consumption", msg="Agendamento não encontrado",
                            success=False, code=404
                        )

                    status = row[0]

                    if status != "AGENDADO":
                        return self.build_response(
                            router="confirm_consumption", msg="Agendamento não encontrado ou já consumido",
                            success=False, code=409
                        )

                    update_query = """
                        UPDATE schedules
                        SET status = 'CONFIRMADO',
                            consumed_at = CURRENT_TIMESTAMP,
                            confirmed_by = %s
                        WHERE id = %s AND status = 'AGENDADO'
                    """
                    cursor.execute(update_query, (employee_id, schedule_id))

                    insert_query = """
                        INSERT INTO consumptions (schedule_id, confirmed_by)
                        VALUES (%s, %s)
                    """
                    cursor.execute(insert_query, (schedule_id, employee_id))

                    return self.build_response(
                        router="confirm_consumption",
                        msg="Consumo confirmado com sucesso"
                    )

        except Exception as exception:
            logger.error(f"Error in confirm_consumption: {exception}")
            return self.build_response(
                router="confirm_consumption", msg=f"Erro inesperado: {exception}", success=False, code=500
            )

    def get_daily_summary(self, target_date: date) -> dict:
        try:
            with self.get_connect() as conn, conn.cursor() as cursor:
                sql_query = """
                        SELECT
                            COUNT(*) AS total_agendados,
                            COUNT(*) FILTER (WHERE status = 'CONFIRMADO') AS consumidos,
                            COUNT(*) FILTER (WHERE status = 'AGENDADO') AS pendentes
                        FROM schedules
                        WHERE schedule_date = %s
                    """

                cursor.execute(sql_query, (target_date,))
                result = cursor.fetchone()

                all_schedules = result[0] or 0
                consumed = result[1] or 0
                pending = result[2] or 0

                data = {
                    "agendados": all_schedules,
                    "consumidos": consumed,
                    "pendentes": pending,
                    "no_shows": all_schedules - consumed
                }

                return self.build_response(
                    router="get_daily_summary", msg="Resumo diário obtido com sucesso", data=data
                )

        except Exception as exception:
            logger.error(f"Error in get_daily_summary: {exception}")
            return self.build_response(
                router="get_daily_summary", msg=f"Erro inesperado: {exception}", success=False, code=500
            )

    def get_consumption_report(self, start_date: date, end_date : date | None = None) -> dict:
        try:
            with self.get_connect() as conn:
                with conn.cursor() as cursor:
                    if end_date:
                        sql_query = """
                            SELECT schedule_date,
                                COUNT(*) AS agendados,
                                COUNT(*) FILTER (WHERE status = 'CONFIRMADO') AS consumidos,
                                COUNT(*) - COUNT(*) FILTER (WHERE status = 'CONFIRMADO') AS no_shows
                            FROM schedules
                            WHERE schedule_date BETWEEN %s AND %s
                            GROUP BY schedule_date
                            ORDER BY schedule_date
                        """
                        cursor.execute(sql_query, (start_date, end_date))
                    else:
                        sql_query = """
                            SELECT schedule_date,
                                COUNT(*) AS agendados,
                                COUNT(*) FILTER (WHERE status = 'CONFIRMADO') AS consumidos,
                                COUNT(*) - COUNT(*) FILTER (WHERE status = 'CONFIRMADO') AS no_shows
                            FROM schedules
                            WHERE schedule_date = %s
                            GROUP BY schedule_date
                            ORDER BY schedule_date
                        """
                        cursor.execute(sql_query, (start_date,))

                    results = cursor.fetchall()

                    if not results:
                        return self.build_response(
                            router="get_consumption_report", msg="Nenhum registro encontrado", success=False, code=404
                        )

                    columns = [desc[0] for desc in cursor.description]
                    data = [dict(zip(columns, row)) for row in results]

                    return self.build_response(
                        router="get_consumption_report", msg="Relatório de consumo gerado com sucesso", data=data
                    )

        except Exception as exception:
            logger.error(f"Error in get_consumption_report: {exception}")
            return self.build_response(
                router="get_consumption_report",
                msg=f"Erro inesperado: {exception}",
                success=False,
                code=500
            )
