from fastapi import APIRouter, Depends, HTTPException, Query

from notification.models import DeviceTokenRequest, QueueCollaborationRequest
from notification.notification_service import (
    NotificationService,
)
from utils.rate_limiter import RateLimiter

router = APIRouter()
notification_service = NotificationService()

# Rate limiters — sliding window per client IP
_daily_reminder_limiter = RateLimiter(max_requests=10, window_seconds=60)
_queue_collab_limiter = RateLimiter(max_requests=5, window_seconds=60)


def _verify_cpf_exists(cpf: str) -> None:
    """Ensure the CPF belongs to a registered user before triggering collaboration."""
    user = notification_service.repository.get_user_by_cpf(cpf)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="CPF não encontrado no sistema. Solicite colaboração apenas com CPF registrado.",
        )


@router.post("/device/register")
def register_device(request: DeviceTokenRequest) -> dict:
    return notification_service.register_device(
        user_cpf=request.user_cpf,
        token=request.token,
        platform=request.platform,
    )


@router.post("/notification/daily-reminder/trigger")
def trigger_daily_reminder(_=Depends(_daily_reminder_limiter)):
    return notification_service.execute_daily_reminder()


@router.post("/notification/queue-collaboration/trigger")
def trigger_queue_collaboration(
    request: QueueCollaborationRequest, _=Depends(_queue_collab_limiter)
):
    _verify_cpf_exists(cpf=request.cpf)
    return notification_service.execute_queue_collaboration(cpf=request.cpf)


@router.get("/notification/jobs")
def list_notification_jobs(
    limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)
) -> dict:
    return notification_service.get_jobs(limit=limit, offset=offset)


@router.get("/notification/jobs/{job_id}")
def get_notification_job(job_id: int) -> dict:
    return notification_service.get_job_status(job_id=job_id)
