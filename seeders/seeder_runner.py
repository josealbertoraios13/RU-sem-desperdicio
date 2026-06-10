"""
Seeder Runner - Gerencia execução de todos os seeds.

Responsável por:
- Orquestrar execução de múltiplos seeds
- Garantir ordem de dependência
- Fornecer endpoint HTTP para execução
- Auto-execução após inicialização do banco
"""

import os
from typing import Any

from seeders.base_seeder import BaseSeeder
from seeders.schedule_seeder import ScheduleSeeder
from seeders.user_seeder import UserSeeder
from utils.logger import logger


class SeederRunner:
    """
    Gerenciador de seeds do sistema.

    Executa seeds em ordem e com tratamento de erros.
    Suporta execução completa ou parcial por módulos.
    """

    def __init__(self, connection_pool=None):
        """
        Inicializa o runner.

        Args:
            connection_pool: Pool de conexões do banco
        """
        self.connection_pool = connection_pool
        self.seeds_executed: list[str] = []
        self.seeds_failed: list[str] = []

    def _get_seed_instance(self, seed_class) -> BaseSeeder:
        """Instancia um seeder com o connection pool."""
        return seed_class(connection_pool=self.connection_pool)

    def execute_seed(
        self,
        seeder: BaseSeeder,
        **kwargs
    ) -> dict[str, Any]:
        """
        Executa um seed individual.

        Args:
            seeder: Instância do seeder a ser executado

        Returns:
            Resultado da execução
        """
        seed_name = getattr(seeder, 'seed_name', 'unknown')
        logger.info(f"Executando seed: {seed_name}")

        try:
            result = seeder.seed(**kwargs)
            self.seeds_executed.append(seed_name)
            logger.info(f"Seed {seed_name} finalizado com sucesso")
            return result
        except Exception as e:
            self.seeds_failed.append(seed_name)
            logger.error(f"Erro no seed {seed_name}: {e}")
            return {
                "seed_name": seed_name,
                "success": False,
                "error": str(e)
            }

    def run_all(self) -> dict[str, Any]:
        """
        Executa todos os seeds em ordem.

        Ordem de execução:
        1. Users (base para outros seeds)
        2. Schedules (depende de users)

        Returns:
            Dict com resumo geral
        """
        logger.info("Iniciando execução de todos os seeds...")
        self.seeds_executed = []
        self.seeds_failed = []

        results = {}

        # 1. User Seeder (obrigatório)
        user_seeder = self._get_seed_instance(UserSeeder)
        results["user_seeder"] = self.execute_seed(user_seeder)

        # 2. Schedule Seeder (opcional, depende de users)
        schedule_seeder = self._get_seed_instance(ScheduleSeeder)
        results["schedule_seeder"] = self.execute_seed(schedule_seeder)

        # Resumo
        success_count = len(self.seeds_executed)
        fail_count = len(self.seeds_failed)

        logger.info(
            f"Execução de seeds finalizada: "
            f"{success_count} sucesso(s), {fail_count} falha(s)"
        )

        return {
            "success": fail_count == 0,
            "seeds_executed": self.seeds_executed,
            "seeds_failed": self.seeds_failed,
            "results": results
        }

    def run_by_name(
        self,
        seed_name: str,
        **kwargs
    ) -> dict[str, Any]:
        """
        Executa um seed específico por nome.

        Args:
            seed_name: Nome do seed a executar

        Returns:
            Resultado da execução
        """
        seeders_map = {
            "user": UserSeeder,
            "schedule": ScheduleSeeder,
        }

        if seed_name not in seeders_map:
            error_msg = f"Seed '{seed_name}' não encontrado"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }

        seeder = self._get_seed_instance(seeders_map[seed_name])
        result = self.execute_seed(seeder, **kwargs)

        return {
            "success": result.get("success", False),
            "seed_name": seed_name,
            "result": result
        }

    def run_by_names(
        self,
        seed_names: list[str],
        **kwargs
    ) -> dict[str, Any]:
        """
        Executa múltiplos seeds específicos.

        Args:
            seed_names: Lista de nomes de seeds

        Returns:
            Resultados consolidados
        """
        results = {}
        for name in seed_names:
            results[name] = self.run_by_name(name, **kwargs)

        success = all(
            r.get("success", False)
            for r in results.values()
        )

        return {
            "success": success,
            "results": results
        }

    def is_executed(self, seed_name: str) -> bool:
        """Verifica se seed já foi executado."""
        return seed_name in self.seeds_executed

    def clear_history(self):
        """Limpa histórico de execução."""
        self.seeds_executed = []
        self.seeds_failed = []


# Instância global para reutilização
_seeder_runner_instance: SeederRunner | None = None


def get_seeder_runner(connection_pool=None) -> SeederRunner:
    """
    Obtém instância singleton do SeederRunner.

    Args:
        connection_pool: Pool de conexões do banco

    Returns:
        Instância do SeederRunner
    """
    global _seeder_runner_instance
    if _seeder_runner_instance is None:
        _seeder_runner_instance = SeederRunner(connection_pool)
    elif connection_pool is not None:
        _seeder_runner_instance.connection_pool = connection_pool
    return _seeder_runner_instance


def get_seeder_runner_with_pool() -> SeederRunner:
    """Retorna o runner com o pool PostgreSQL inicializado (uso em HTTP e startup)."""
    from repository.repository import Repository

    repository = Repository()
    repository._ensure_pool()
    return get_seeder_runner(connection_pool=Repository._connection_pool)


def run_seeds_on_startup(connection_pool=None) -> dict[str, Any]:
    """
    Executa seeds automaticamente na inicialização.

    Args:
        connection_pool: Pool de conexões do banco

    Returns:
        Resultado da execução
    """
    # Verifica se deve rodar seeds (padrão: True em dev/test)
    run_on_startup = os.getenv("RUN_SEED_ON_STARTUP", "true").lower()
    if run_on_startup not in ("true", "1", "yes"):
        logger.info("Seed on startup desativado via variável de ambiente")
        return {"success": True, "message": "Seed desativado"}

    logger.info("Auto-executando seeds na inicialização...")
    runner = SeederRunner(connection_pool)
    return runner.run_all()
