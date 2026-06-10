import os
import threading

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Notification system
from notification import notification_router
from notification import start_scheduler as start_notification_scheduler
from paths import PROJECT_ROOT
from routers import (
    menu_router,
    report_router,
    schedule_router,
    seed_router,
    user_router,
)
from utils.logger import logger

load_dotenv(PROJECT_ROOT / ".env")

url = os.getenv("SMART_RU_URL")
if not url:
    url = "http://127.0.0.1:8000"

origins = ["*"]

cors_origins_env = os.getenv("CORS_ORIGINS")
if cors_origins_env:
    extra_origins = [origin.strip() for origin in cors_origins_env.split(",")]
    origins.extend(extra_origins)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router.router, prefix="/api")
app.include_router(schedule_router.router, prefix="/api")
app.include_router(report_router.router, prefix="/api")
app.include_router(seed_router.router, prefix="/api")
app.include_router(menu_router.router, prefix="/api")

app.include_router(notification_router, prefix="/api")

@app.get("/api/status")
def read_root():
    return {"message": "Olá, sua API do Smart RU está rodando!"}


def run_seeds_on_startup():
    run_seed = os.getenv("RUN_SEED_ON_STARTUP", "true").lower()
    if run_seed not in ("true", "1", "yes"):
        logger.info("Seed on startup desativado via variável de ambiente")
        return
    try:
        logger.info("Auto-executando seeds na inicialização...")
        from seeders.seeder_runner import get_seeder_runner_with_pool

        result = get_seeder_runner_with_pool().run_all()
        logger.info(f"Seeds finalizados: {result}")
    except Exception as e:
        logger.error(f"Erro na auto-execução de seeds: {e}")


def _delayed_seed():
    import time

    time.sleep(2)
    run_seeds_on_startup()


def _start_scheduler():
    """Start the APScheduler for notification jobs in a background thread."""
    try:
        start_notification_scheduler()
        logger.info("Sistema de notificações agendadas iniciado com sucesso!")
    except Exception as e:
        logger.error(f"Erro ao iniciar scheduler de notificações: {e}")


threading.Thread(target=_delayed_seed, daemon=True).start()
threading.Thread(target=_start_scheduler, daemon=True).start()
