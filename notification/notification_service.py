from datetime import UTC, datetime
from enum import StrEnum

from smartru.notification.channels.email_channel import (
    EmailNotificationChannel,
)
from smartru.notification.channels.push_channel import PushChannel
from smartru.notification.templates.render import (
    render_daily_reminder_email,
    render_daily_reminder_push,
    render_queue_collaboration_email,
    render_queue_collaboration_push,
    render_schedule_reminder_email,
    render_schedule_reminder_push,
)
from smartru.repository.notification.notification_repository import (
    NotificationRepository,
)
from smartru.services.service import Service
from smartru.utils import logger


class NotificationType(StrEnum):
    DAILY_REMINDER = "daily_reminder"
    QUEUE_COLLABORATION = "queue_collaboration"


class NotificationService(Service):
    def __init__(self):
        self.repository = NotificationRepository()
        self.push_channel = PushChannel()
        self.email_channel = EmailNotificationChannel()

    def register_device(self, user_cpf: str, token: str, platform: str) -> dict:
        """Register or update a device token for push notifications."""
        result = self.repository.register_device_token(
            user_cpf=user_cpf, token=token, platform=platform
        )
        return self.handle_response(response=result)

    def execute_daily_reminder(self, scheduled_at: datetime | None = None) -> dict:

        scheduled_at = scheduled_at or datetime.now(UTC)
        target_users = self.repository.get_target_users()

        return self._execute_job(
            target_users=target_users,
            job_type=NotificationType.DAILY_REMINDER.value,
            scheduled_at=scheduled_at,
        )

    def execute_queue_collaboration(self, cpf: str, scheduled_at: datetime | None = None) -> dict:

        scheduled_at = scheduled_at or datetime.now(UTC)
        target_users = self.repository.get_target_users(exclude_cpf=cpf)

        # Look up the requester's name for collaboration notification templates
        requester = self.repository.get_user_by_cpf(cpf)
        requester_name = requester["name"] if requester else "Alguém"

        return self._execute_job(
            target_users=target_users,
            job_type=NotificationType.QUEUE_COLLABORATION.value,
            scheduled_at=scheduled_at,
            requester_name=requester_name,
        )

    def _execute_job(
        self,
        target_users: list,
        job_type: str,
        scheduled_at: datetime,
        requester_name: str | None = None,
    ) -> dict:
        if not target_users:
            logger.warning(f"{job_type}: no target users found")
            return {
                "job_id": None,
                "total_users": 0,
                "success_count": 0,
                "failure_count": 0,
                "message": "Nenhum usuário alvo encontrado",
            }

        job_result = self.repository.create_job(
            job_type=job_type, scheduled_at=scheduled_at, total_users=len(target_users)
        )

        if not job_result.get("success"):
            logger.error(f"{job_type}: failed to create job tracking record")
            return {
                "job_id": None,
                "total_users": len(target_users),
                "success_count": 0,
                "failure_count": len(target_users),
                "message": "Falha ao criar job de notificação",
            }

        job_id = job_result["data"]["job_id"]
        self.repository.update_job_status(job_id=job_id, status="running")

        success_count = 0
        failure_count = 0

        for user in target_users:
            user_ok = self._notify_single_user(
                user_cpf=user["cpf"],
                user_name=user["name"],
                user_email=user["email"],
                job_id=job_id,
                notification_type=job_type,
                requester_name=requester_name,
            )

            if user_ok:
                success_count += 1
            else:
                failure_count += 1

        # Finalize job
        if failure_count == 0:
            final_status = "completed"
        elif success_count > 0:
            final_status = "partial"
        else:
            final_status = "failed"

        self.repository.update_job_status(
            job_id=job_id,
            status=final_status,
            success_count=success_count,
            failure_count=failure_count,
        )

        logger.info(
            f"{job_type} job #{job_id} completed: "
            f"{success_count}/{len(target_users)} sent "
            f"({failure_count} failures)"
        )

        return {
            "job_id": job_id,
            "total_users": len(target_users),
            "success_count": success_count,
            "failure_count": failure_count,
            "message": (
                f"Job {final_status}: {success_count}/{len(target_users)} notificações enviadas"
            ),
        }

    def execute_schedule_reminder(self) -> dict:
        schedules = self.repository.get_schedules_for_reminder()

        if not schedules:
            logger.info("Schedule Reminder: no upcoming schedules found")
            return {
                "total": 0,
                "success_count": 0,
                "failure_count": 0,
                "message": "Nenhum agendamento próximo encontrado",
            }

        success_count = 0
        failure_count = 0

        for schedule in schedules:
            estimated_time = str(schedule["estimated_time"])[:5]

            sent = self._notify_schedule_reminder(
                user_cpf=schedule["user_cpf"],
                user_name=schedule["name"],
                user_email=schedule["email"],
                schedule_id=schedule["id"],
                schedule_type=schedule["schedule_type"],
                estimated_time=estimated_time,
            )

            if sent:
                self.repository.mark_reminder_sent(schedule["id"])
                success_count += 1
            else:
                failure_count += 1

        logger.info(
            f"Schedule reminder: {success_count}/{len(schedules)} sent Failures: {failure_count}"
        )

        return {
            "total": len(schedules),
            "success_count": success_count,
            "failure_count": failure_count,
            "message": f"{success_count}/{len(schedules)} lembretes enviados",
        }

    def _notify_single_user(
        self,
        user_cpf: str,
        user_name: str,
        user_email: str,
        job_id: int,
        notification_type: str = NotificationType.DAILY_REMINDER.value,
        requester_name: str | None = None,
    ) -> bool:
        active_tokens = self.repository.get_user_active_tokens(user_cpf)

        if active_tokens:
            # Try push notification first
            if self._send_push(
                user_cpf=user_cpf,
                user_name=user_name,
                active_tokens=active_tokens,
                job_id=job_id,
                notification_type=notification_type,
                requester_name=requester_name,
            ):
                return True

            # Push failed for all tokens, fall through to email
            logger.info(f"Push failed for {user_cpf}, falling back to email")

        # Fallback: email notification
        return self._send_email(
            user_cpf=user_cpf,
            user_name=user_name,
            user_email=user_email,
            job_id=job_id,
            notification_type=notification_type,
            requester_name=requester_name,
        )

    def _notify_schedule_reminder(
        self,
        user_cpf: str,
        user_name: str,
        user_email: str,
        schedule_id: int,
        schedule_type: str,
        estimated_time: str,
    ) -> bool:
        active_tokens = self.repository.get_user_active_tokens(user_cpf=user_cpf)

        if active_tokens:
            if self._send_schedule_reminder_push(
                user_cpf=user_cpf,
                user_name=user_name,
                active_tokens=active_tokens,
                schedule_type=schedule_type,
                estimated_time=estimated_time,
            ):
                return True

            logger.info(f"Push reminder failed for {user_cpf},  falling back to email")

        return self._send_schedule_reminder_email(
            user_cpf=user_cpf,
            user_name=user_name,
            user_email=user_email,
            schedule_type=schedule_type,
            estimated_time=estimated_time,
        )

    def _send_push(
        self,
        user_cpf: str,
        user_name: str,
        active_tokens: list[dict],
        job_id: int,
        notification_type: str = NotificationType.DAILY_REMINDER.value,
        requester_name: str | None = None,
    ) -> bool:
        """Send push notification. Returns True if any token succeeds."""
        if notification_type == NotificationType.QUEUE_COLLABORATION.value:
            template = render_queue_collaboration_push(name=requester_name or "Alguém")
        else:
            template = render_daily_reminder_push(name=user_name)

        notif_result = self.repository.create_notification(
            user_cpf=user_cpf,
            channel="push",
            title=template["title"],
            message=template["message"],
            job_id=job_id,
        )
        if not notif_result.get("success"):
            return False

        notification_id = notif_result["data"]["notification_id"]

        # Try each active token; succeed if any succeeds
        for token_info in active_tokens:
            result = self.push_channel.send(
                user_cpf=user_cpf,
                title=template["title"],
                message=template["message"],
                device_token=token_info["token"],
            )

            if result["success"]:
                self.repository.update_notification_status(
                    notification_id=notification_id, status="sent"
                )
                return True

            # Token is invalid/unregistered → deactivate it
            if result.get("needs_token_deactivation"):
                self.repository.deactivate_device_token(token_info["token"])

        # All tokens failed
        self.repository.update_notification_status(
            notification_id=notification_id,
            status="failed",
            error_message="Todos os tokens de push falharam",
        )
        return False

    def _send_schedule_reminder_push(
        self,
        user_cpf: str,
        user_name: str,
        active_tokens: list[dict],
        schedule_type: str,
        estimated_time: str,
    ) -> bool:
        template = render_schedule_reminder_push(
            name=user_name, schedule_type=schedule_type, estimated_time=estimated_time
        )

        notif_result = self.repository.create_notification(
            user_cpf=user_cpf, channel="push", title=template["title"], message=template["message"]
        )

        if not notif_result.get("success"):
            return False

        notification_id = notif_result["data"]["notification_id"]

        for token_info in active_tokens:
            result = self.push_channel.send(
                user_cpf=user_cpf,
                title=template["title"],
                message=template["message"],
                device_token=token_info["token"],
            )

            if result["success"]:
                self.repository.update_notification_status(
                    notification_id=notification_id, status="sent"
                )
                return True

            if result.get("needs_token_deactivation"):
                self.repository.deactivate_device_token(token_info["token"])

        self.repository.update_notification_status(
            notification_id=notification_id,
            status="failed",
            error_message="Todos os tokens de push falharam",
        )

        return False

    def _send_email(
        self,
        user_cpf: str,
        user_name: str,
        user_email: str,
        job_id: int,
        notification_type: str = NotificationType.DAILY_REMINDER.value,
        requester_name: str | None = None,
    ) -> bool:
        if notification_type == NotificationType.QUEUE_COLLABORATION.value:
            subject, html_body = render_queue_collaboration_email(name=requester_name or "Alguém")
        else:
            subject, html_body = render_daily_reminder_email(name=user_name, email=user_email)

        notif_result = self.repository.create_notification(
            user_cpf=user_cpf,
            channel="email",
            title=subject,
            message=html_body,
            job_id=job_id,
        )

        if not notif_result.get("success"):
            return False

        notification_id = notif_result["data"]["notification_id"]

        result = self.email_channel.send(
            user_cpf=user_cpf,
            title=subject,
            message=html_body,
            user_email=user_email,
            user_name=user_name,
        )

        if result["success"]:
            self.repository.update_notification_status(
                notification_id=notification_id, status="sent"
            )
            return True
        else:
            self.repository.update_notification_status(
                notification_id=notification_id,
                status="failed",
                error_message=result.get("error_message"),
            )
            return False

    def _send_schedule_reminder_email(
        self,
        user_cpf: str,
        user_name: str,
        user_email: str,
        schedule_type: str,
        estimated_time: str,
    ) -> bool:
        subject, html_body = render_schedule_reminder_email(
            name=user_name, schedule_type=schedule_type, estimated_time=estimated_time
        )

        notif_result = self.repository.create_notification(
            user_cpf=user_cpf, channel="email", title=subject, message=html_body
        )

        if not notif_result.get("success"):
            return False

        notification_id = notif_result["data"]["notification_id"]

        result = self.email_channel.send(
            user_cpf=user_cpf,
            title=subject,
            message=html_body,
            user_email=user_email,
            user_name=user_name,
        )

        if result["success"]:
            self.repository.update_notification_status(
                notification_id=notification_id, status="sent"
            )
            return True

        self.repository.update_notification_status(
            notification_id=notification_id,
            status="failed",
            error_message=result.get("error_message"),
        )

        return False

    # NOTIFICATION HISTORY
    def get_user_notifications(self, user_cpf: str, limit: int = 20, offset: int = 0) -> dict:
        """Get notification history for a specific user."""
        notifications = self.repository.get_user_notifications(
            user_cpf=user_cpf, limit=limit, offset=offset
        )
        return self.handle_response(
            response={
                "success": True,
                "router": "get_user_notifications",
                "part": "notification_service",
                "msg": (
                    f"{len(notifications)} notificações encontradas"
                    if notifications
                    else "Nenhuma notificação encontrada"
                ),
                "data": notifications,
            }
        )

    def get_job_status(self, job_id: int) -> dict:
        """Get the status of a specific notification job."""
        job = self.repository.get_job(job_id=job_id)
        if not job:
            self.raise_exception(404, "Job de notificação não encontrado")
        return self.handle_response(
            response={
                "success": True,
                "router": "get_job_status",
                "part": "notification_service",
                "msg": "Job encontrado",
                "data": job,
            }
        )

    def get_jobs(self, limit: int = 20, offset: int = 0) -> dict:
        """List recent notification jobs."""
        jobs = self.repository.get_jobs(limit=limit, offset=offset)
        return self.handle_response(
            response={
                "success": True,
                "router": "get_jobs",
                "part": "notification_service",
                "msg": (f"{len(jobs)} jobs encontrados" if jobs else "Nenhum job encontrado"),
                "data": jobs,
            }
        )
