"""
Rota de seed para popular ambiente de desenvolvimento.
"""

import os

from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from seeders.seeder_runner import SeederRunner, get_seeder_runner_with_pool
from utils.logger import logger

router = APIRouter(prefix="/seed", tags=["seed"])
security = HTTPBearer(auto_error=False)


def get_runner() -> SeederRunner:
    return get_seeder_runner_with_pool()


def verify_admin_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """
    Verifica se o token de autentcação é válido para operações admin.

    O token é definido via variável de ambiente ADMIN_API_KEY.
    """
    admin_key = os.getenv("ADMIN_API_KEY")

    if not admin_key:
        logger.warning("ADMIN_API_KEY not configured - seed endpoint disabled")
        raise HTTPException(
            status_code=503,
            detail="Seed endpoint not configured. Contact administrator."
        )

    if not credentials or credentials.credentials != admin_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing admin authentication token"
        )

    return "admin"


@router.post("/", dependencies=[Depends(verify_admin_token)])
async def run_seed(
    seed_name: str | None = None,
    seeds: list[str] | None = None
):
    """
    Executa seeds no banco de dados.

    Args:
        seed_name: Nome do seed específico a executar (opcional)
        seeds: Lista de seeds para executar (opcional)

    Returns:
        Resultado da execução

    Examples:
        POST /seed/              - Executa todos os seeds
        POST /seed/?seed_name=user - Executa apenas seed de usuários
        POST /seed/?seeds=user,schedule - Executa seeds específicos
    """
    try:
        # Obtém pool de conexões atual
        runner = get_runner()

        # Executa seeds específicos
        if seeds:
            result = runner.run_by_names(seeds)
        elif seed_name:
            result = runner.run_by_name(seed_name)
        else:
            # Executa todos
            result = runner.run_all()

        if not result.get("success", False):
            raise HTTPException(
                status_code=500,
                detail={
                    "success": False,
                    "message": "Erro na execução do seed",
                    "details": result
                }
            )

        return {
            "success": True,
            "message": "Seed executado com sucesso",
            "data": result
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao executar seed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": str(e)
            }
        )


@router.get("/status", dependencies=[Depends(verify_admin_token)])
async def seed_status():
    """
    Retorna status dos seeds executados.

    Returns:
        Status atual dos seeds
    """
    runner = get_runner()
    return {
        "seeds_executed": runner.seeds_executed,
        "seeds_failed": runner.seeds_failed,
        "last_run": "available" if runner.seeds_executed else "none"
    }
