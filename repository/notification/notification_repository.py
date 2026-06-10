from datetime import UTC, datetime

from smartru.repository.repository import Repository
from smartru.utils import logger


class NotificationRepository(Repository):
    PART = "notification_repository"

    def register_device_token(self, user_cpf: str, token: str, platform: str) -> dict:
        try:
            with self.get_connect() as conn, conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM device_tokens WHERE token = %s",
                    (token,),
                )
                existing = cursor.fetchone()
                now = datetime.now(UTC)

                if existing:
                    cursor.execute(
                        """UPDATE device_tokens
                           SET is_active = TRUE, platform = %s, updated_at = %s
                           WHERE token = %s""",
                        (platform, now, token),
                    )
                    msg = "Dispositivo atualizado com sucesso!"
                else:
                    cursor.execute(
                        """INSERT INTO device_tokens
                               (user_cpf, token, platform, created_at, updated_at)
                           VALUES (%s, %s, %s, %s, %s)""",
                        (user_cpf, token, platform, now, now),
                    )
                    msg = "Dispositivo registrado com sucesso para notificações!"

                return self.build_response(router="register_device_token", msg=msg)

        except Exception as e:
            logger.error(f"Error in register_device_token: {e}")
            return self.build_response(
                router="register_device_token",
                msg=f"Erro ao registrar dispositivo: {e}",
                success=False,
                code=500,
            )

    def deactivate_device_token(self, token: str) -> None:
        try:
            with self.get_connect() as conn, conn.cursor() as cursor:
                cursor.execute(
                    """UPDATE device_tokens
                       SET is_active = FALSE, updated_at = %s
                       WHERE token = %s""",
                    (datetime.now(UTC), token),
                )
        except Exception as e:
            logger.error(f"Error deactivating device token: {e}")

    def get_user_active_tokens(self, user_cpf: str) -> list[dict]:
        try:
            with self.get_connect() as conn, conn.cursor() as cursor:
                cursor.execute(
                    """SELECT id, token, platform
                       FROM device_tokens
                       WHERE user_cpf = %s AND is_active = TRUE
                       ORDER BY updated_at DESC""",
                    (user_cpf,),
                )
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error in get_user_active_tokens: {e}")
            return []

    def get_target_users(self, exclude_cpf: str | None = None) -> list[dict]:
        try:
            with self.get_connect() as conn, conn.cursor() as cursor:
                if exclude_cpf:
                    cursor.execute(
                        """SELECT cpf, name, email
                        FROM users
                        WHERE role IN ('estudante', 'convidado')
                        AND cpf != %s
                        ORDER BY name""",
                        (exclude_cpf,),
                    )
                else:
                    cursor.execute(
                        """SELECT cpf, name, email
                        FROM users
                        WHERE role IN ('estudante', 'convidado')
                        ORDER BY name"""
                    )

                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error in get_target_users: {e}")
            return []

    def create_job(self, job_type: str, scheduled_at: datetime, total_users: int = 0) -> dict:
        try:
            with self.get_connect() as conn, conn.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO notification_jobs
                           (job_type, scheduled_at, total_users, status)
                       VALUES (%s, %s, %s, 'scheduled')
                       RETURNING id""",
                    (job_type, scheduled_at, total_users),
                )
                job_id = cursor.fetchone()[0]
                return self.build_response(
                    router="create_job",
                    msg="Job de notificação criado",
                    data={"job_id": job_id},
                )
        except Exception as e:
            logger.error(f"Error in create_job: {e}")
            return self.build_response(
                router="create_job",
                msg=f"Erro ao criar job: {e}",
                success=False,
                code=500,
            )

    def update_job_status(
        self,
        job_id: int,
        status: str,
        success_count: int | None = None,
        failure_count: int | None = None,
        error_message: str | None = None,
    ) -> None:
        try:
            now = datetime.now(UTC)
            with self.get_connect() as conn, conn.cursor() as cursor:
                cursor.execute(
                    """UPDATE notification_jobs
                       SET status = %s,
                           success_count = %s,
                           failure_count = %s,
                           error_message = %s,
                           executed_at = COALESCE(executed_at, %s),
                           completed_at = CASE
                               WHEN %s IN ('completed', 'failed', 'partial')
                               THEN %s ELSE completed_at
                           END
                       WHERE id = %s""",
                    (
                        status,
                        success_count if success_count is not None else 0,
                        failure_count if failure_count is not None else 0,
                        error_message,
                        now if status == "running" else None,
                        status,
                        now if status in ("completed", "failed", "partial") else None,
                        job_id,
                    ),
                )
        except Exception as e:
            logger.error(f"Error updating job {job_id}: {e}")

    def get_last_job_of_type(self, job_type: str) -> dict | None:
        try:
            with self.get_connect() as conn, conn.cursor() as cursor:
                cursor.execute(
                    """SELECT id, job_type, scheduled_at, executed_at,
                              completed_at, status, total_users,
                              success_count, failure_count, error_message
                       FROM notification_jobs
                       WHERE job_type = %s
                       ORDER BY scheduled_at DESC LIMIT 1""",
                    (job_type,),
                )
                row = cursor.fetchone()
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    return dict(zip(columns, row))
                return None
        except Exception as e:
            logger.error(f"Error in get_last_job_of_type: {e}")
            return None

    def create_notification(
        self,
        user_cpf: str,
        channel: str,
        title: str,
        message: str,
        job_id: int | None = None,
        max_retries: int = 3,
    ) -> dict:
        try:
            with self.get_connect() as conn, conn.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO notifications
                           (user_cpf, channel, title, message, status,
                            job_id, max_retries, created_at)
                       VALUES (%s, %s, %s, %s, 'pending', %s, %s, %s)
                       RETURNING id""",
                    (
                        user_cpf,
                        channel,
                        title,
                        message,
                        job_id,
                        max_retries,
                        datetime.now(UTC),
                    ),
                )
                notif_id = cursor.fetchone()[0]
                return self.build_response(
                    router="create_notification",
                    msg="Notificação registrada",
                    data={"notification_id": notif_id},
                )
        except Exception as e:
            logger.error(f"Error in create_notification: {e}")
            return self.build_response(
                router="create_notification",
                msg=f"Erro ao registrar notificação: {e}",
                success=False,
                code=500,
            )

    def update_notification_status(
        self, notification_id: int, status: str, error_message: str | None = None
    ) -> None:
        try:
            with self.get_connect() as conn, conn.cursor() as cursor:
                cursor.execute(
                    """UPDATE notifications
                       SET status = %s,
                           sent_at = CASE WHEN %s = 'sent' THEN %s ELSE sent_at END,
                           error_message = %s
                       WHERE id = %s""",
                    (
                        status,
                        status,
                        datetime.now(UTC) if status == "sent" else None,
                        error_message,
                        notification_id,
                    ),
                )
        except Exception as e:
            logger.error(f"Error updating notification {notification_id}: {e}")

    def get_user_notifications(self, user_cpf: str, limit: int = 20, offset: int = 0) -> list[dict]:
        try:
            with self.get_connect() as conn, conn.cursor() as cursor:
                cursor.execute(
                    """SELECT id, channel, title, message, status,
                              sent_at, error_message, retry_count, created_at
                       FROM notifications
                       WHERE user_cpf = %s
                       ORDER BY created_at DESC
                       LIMIT %s OFFSET %s""",
                    (user_cpf, limit, offset),
                )
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error in get_user_notifications: {e}")
            return []

    def get_job(self, job_id: int) -> dict | None:
        try:
            with self.get_connect() as conn, conn.cursor() as cursor:
                cursor.execute(
                    """SELECT id, job_type, scheduled_at, executed_at,
                              completed_at, status, total_users,
                              success_count, failure_count, error_message,
                              created_at
                       FROM notification_jobs
                       WHERE id = %s""",
                    (job_id,),
                )
                row = cursor.fetchone()
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    return dict(zip(columns, row))
                return None
        except Exception as e:
            logger.error(f"Error in get_job: {e}")
            return None

    def get_jobs(self, limit: int = 20, offset: int = 0) -> list[dict]:
        try:
            with self.get_connect() as conn, conn.cursor() as cursor:
                cursor.execute(
                    """SELECT id, job_type, scheduled_at, executed_at,
                              completed_at, status, total_users,
                              success_count, failure_count, created_at
                       FROM notification_jobs
                       ORDER BY created_at DESC
                       LIMIT %s OFFSET %s""",
                    (limit, offset),
                )
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error in get_jobs: {e}")
            return []

    def get_pending_retries(self, limit: int = 50) -> list[dict]:
        try:
            with self.get_connect() as conn, conn.cursor() as cursor:
                cursor.execute(
                    """SELECT id, user_cpf, channel, title, message,
                              retry_count, max_retries
                       FROM notifications
                       WHERE status = 'failed'
                         AND retry_count < max_retries
                         AND (next_retry_at IS NULL
                              OR next_retry_at <= %s)
                       LIMIT %s""",
                    (datetime.now(UTC), limit),
                )
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error in get_pending_retries: {e}")
            return []

    def update_notification_retry(self, notification_id: int, success: bool) -> None:
        try:
            with self.get_connect() as conn, conn.cursor() as cursor:
                cursor.execute(
                    """UPDATE notifications
                       SET retry_count = retry_count + 1,
                           next_retry_at = CASE
                               WHEN %s THEN NULL
                               ELSE %s + INTERVAL '15 minutes'
                           END
                       WHERE id = %s""",
                    (success, datetime.now(UTC), notification_id),
                )
        except Exception as e:
            logger.error(f"Error updating retry for notification {notification_id}: {e}")

    def get_user_by_cpf(self, cpf: str) -> dict | None:
        try:
            with self.get_connect() as conn, conn.cursor() as cursor:
                cursor.execute(
                    "SELECT name, email FROM users WHERE cpf = %s",
                    (cpf,),
                )
                row = cursor.fetchone()
                if row:
                    return {"name": row[0], "email": row[1]}
                return None
        except Exception as e:
            logger.error(f"Error in get_user_by_cpf: {e}")
            return None

    def get_schedules_for_reminder(self) -> list[dict]:
        try:
            with self.get_connect() as conn, conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT s.id, s.user_cpf, s.schedule_type, s.schedule_date, s.estimated_time, u.name, u.email
                    FROM schedules s
                    JOIN users u ON u.cpf = s.user_cpf
                    WHERE s.schedule_date = CURRENT_DATE
                        AND s.status = 'AGENDADO'
                        AND s.reminder_sent = FALSE
                        AND (s.estimated_time - CURRENT_TIME)
                            BETWEEN INTERVAL '25 minutes'
                                AND INTERVAL '35 minutes'
                    ORDER BY s.estimated_time
                    """,
                )
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error in get_schedules_for_reminder: {e}")
            return []

    def mark_reminder_sent(self, schedule_id: int) -> None:
        try:
            with self.get_connect() as conn, conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE schedules
                    SET reminder_sent = TRUE
                    WHERE id = %s
                    """,
                    (schedule_id,),
                )
        except Exception as e:
            logger.error(f"Error in mark_reminder_sent: {e}")
