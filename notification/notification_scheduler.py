"""
APScheduler integration for the Smart Notification System.

Manages scheduled jobs using an in-memory job store with automatic
recovery: on startup, checks if today's daily reminder has already
run and executes it if missed.

Architecture note:
Using in-memory job store (not SQLAlchemy) to avoid adding a heavy
dependency. Recovery is handled via the notification_jobs DB table.
For multi-container deployments, scheduler_locks table prevents
duplicate execution.

Time zone: America/Sao_Paulo (BRT, used by UFRPE)
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from smartru.notification.notification_service import (
    NotificationService,
)
from smartru.utils import logger

_scheduler: BackgroundScheduler | None = None
_service = NotificationService()

def _daily_reminder_job():
    """Execute the daily reminder notification (called by scheduler)."""
    logger.info("APScheduler: executing daily reminder job")
    result = _service.execute_daily_reminder()
    logger.info(f"APScheduler: daily reminder result — {result.get('message', 'N/A')}")

def _schedule_reminder_job():
    """Send 30-minute reminders for upcoming scheduled meals."""
    logger.info("APScheduler: executing schedule reminder job")
    result = _service.execute_schedule_reminder()
    logger.info(f"APScheduler: schedule reminder result — {result.get('message', 'N/A')}")

def _retry_cleanup_job():
    pending = _service.repository.get_pending_retries(limit=50)
    if not pending:
        return

    logger.info(f"APScheduler: retrying {len(pending)} failed notifications")
    retried = 0
    succeeded = 0

    for notif in pending:
        if notif["channel"] == "push":
            push_ok = _do_push_retry(notif)
            _service.repository.update_notification_retry(
                notif["id"], push_ok
            )
            if push_ok:
                _service.repository.update_notification_status(
                    notif["id"], status="sent"
                )
                succeeded += 1
            retried += 1

        elif notif["channel"] == "email":
            email_ok = _do_email_retry(notif)
            _service.repository.update_notification_retry(
                notif["id"], email_ok
            )
            if email_ok:
                _service.repository.update_notification_status(
                    notif["id"], status="sent"
                )
                succeeded += 1
            retried += 1

    logger.info(
        f"APScheduler: retry cleanup — {succeeded}/{retried} recovered"
    )


def _do_push_retry(notif: dict) -> bool:
    user_data = _service.repository.get_user_active_tokens(
        notif["user_cpf"]
    )
    if not user_data:
        return False

    for token_info in user_data:
        result = _service.push_channel.send(
            user_cpf=notif["user_cpf"],
            title=notif["title"],
            message=notif["message"],
            device_token=token_info["token"],
        )
        if result["success"]:
            return True

        # Token is invalid/unregistered → deactivate it
        if result.get("needs_token_deactivation"):
            _service.repository.deactivate_device_token(
                token_info["token"]
            )

    return False

def _do_email_retry(notif: dict) -> bool:
    user_info = _service.repository.get_user_by_cpf(notif["user_cpf"])
    if not user_info or not user_info.get("email"):
        return False

    result = _service.email_channel.send(
        user_cpf=notif["user_cpf"],
        title=notif["title"],
        message=notif["message"],
        user_email=user_info["email"],
        user_name=user_info.get("name"),
    )
    return result["success"]

# Scheduler lifecycle
def start_scheduler() -> BackgroundScheduler:
    global _scheduler

    if _scheduler is not None and _scheduler.running:
        logger.warning("APScheduler is already running")
        return _scheduler

    _scheduler = BackgroundScheduler(
        job_defaults={
            "coalesce": True,
            "max_instances": 1,
            "misfire_grace_time": 3600,  # 1 hour grace for missed jobs
        },
    )

    # Time zone for UFRPE (Pernambuco)
    tz = "America/Recife"

    # 1. Daily reminder at 11:00 AM BRT
    _scheduler.add_job(
        _daily_reminder_job,
        CronTrigger(hour=11, minute=0, timezone=tz),
        id="daily_reminder",
        replace_existing=True,
        name="Lembrete diário do RU (11:00)",
    )

    # 2. Retry cleanup every 15 minutes
    _scheduler.add_job(
        _retry_cleanup_job,
        CronTrigger(minute="*/15", timezone=tz),
        id="retry_failed_notifications",
        replace_existing=True,
        name="Retry de notificações falhas",
    )

    _scheduler.add_job(
        _schedule_reminder_job,
        CronTrigger(minute="*/5", timezone=tz),
        id="schedule_reminder",
        replace_existing=True,
        name="Lembrete de agendamento (a cada 5min)"
    )

    _scheduler.start()
    logger.info(
        "APScheduler iniciado com sucesso! "
        "Jobs: daily_reminder (11:00 BRT), retry_cleanup (a cada 15min)"
    )

    # Check for missed job after scheduler starts
    _check_missed_job(tz)

    return _scheduler


def _check_missed_job(tz: str) -> None:
    from datetime import date

    try:
        last_job = _service.repository.get_last_job_of_type("daily_reminder")

        # No job has ever run → definitely missed
        if last_job is None:
            logger.info(
                "No daily reminder job found. Executing recovery now..."
            )
            _daily_reminder_job()
            return

        today = date.today()

        # Compute the job's scheduled date (may be a date or datetime)
        if last_job.get("scheduled_at"):
            job_date = last_job["scheduled_at"].date() \
                if hasattr(last_job["scheduled_at"], "date") \
                else last_job["scheduled_at"]
        else:
            job_date = None

        # Only skip when the last job is from today AND completed
        if job_date == today and last_job.get("status") == "completed":
            logger.info(
                "Today's daily reminder already completed. Skipping recovery."
            )
            return

        # Everything else means the job was missed
        logger.info(
            "Today's daily reminder was missed. Executing recovery now..."
        )
        _daily_reminder_job()

    except Exception as e:
        logger.error(f"Error checking missed job: {e}")


def stop_scheduler() -> None:
    """Gracefully shut down the scheduler."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("APScheduler finalizado")
