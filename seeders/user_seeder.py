"""
Seed de usuários - Estudantes e Funcionários.

Responsável por popular a tabela de usuários com:
- 30 estudantes (com CPF e matrícula fornecidos)
- 4 funcionários (com CPF e código funcional)

Idempotente: verifica CPF antes de inserir.
"""

from typing import Any

from seeders.base_seeder import BaseSeeder
from utils.logger import logger
from utils.repository.repository_utils import RepositoryUtils

# Dados fornecidos para seeding
STUDENTS_DATA = [
    {"cpf": "48291730561", "enrollment": "202412837"},
    {"cpf": "73916420855", "enrollment": "202498312"},
    {"cpf": "61502894733", "enrollment": "202476501"},
    {"cpf": "90357261488", "enrollment": "202489776"},
    {"cpf": "15487623907", "enrollment": "202455192"},
    {"cpf": "26850391744", "enrollment": "202401783"},
    {"cpf": "81723640952", "enrollment": "202433905"},
    {"cpf": "59017386421", "enrollment": "202467218"},
    {"cpf": "32486597018", "enrollment": "202410659"},
    {"cpf": "67190428539", "enrollment": "202493044"},
    {"cpf": "23874651097", "enrollment": "202421376"},
    {"cpf": "45901736288", "enrollment": "202485901"},
    {"cpf": "72053816490", "enrollment": "202406732"},
    {"cpf": "98361420577", "enrollment": "202439118"},
    {"cpf": "10593728466", "enrollment": "202477250"},
    {"cpf": "84620573911", "enrollment": "202414805"},
    {"cpf": "31759468203", "enrollment": "202495620"},
    {"cpf": "65930287144", "enrollment": "202452937"},
    {"cpf": "29481650372", "enrollment": "202426509"},
    {"cpf": "57890324615", "enrollment": "202409883"},
    {"cpf": "83276401599", "enrollment": "202468430"},
    {"cpf": "14620875933", "enrollment": "202440765"},
    {"cpf": "90531764208", "enrollment": "202419250"},
    {"cpf": "76352091486", "enrollment": "202491378"},
    {"cpf": "41896523077", "enrollment": "202463512"},
    {"cpf": "25073194682", "enrollment": "202428904"},
    {"cpf": "69710582433", "enrollment": "202473106"},
    {"cpf": "83461257019", "enrollment": "202407990"},
    {"cpf": "56294710388", "enrollment": "202456743"},
    {"cpf": "17983652044", "enrollment": "202432187"},
]

EMPLOYEES_DATA = [
    {"cpf": "15179896045", "enrollment": "FUNC-1029"},
    {"cpf": "65017397051", "enrollment": "FUNC-1184"},
    {"cpf": "37867314032", "enrollment": "FUNC-1357"},
    {"cpf": "36559778088", "enrollment": "FUNC-1492"},
]

# Senhas padrão por tipo de usuário
DEFAULT_PASSWORD = "026!"


class UserSeeder(BaseSeeder):
    """Seeder para tabela de usuários."""

    seed_name = "user_seeder"
    required_fields = ["cpf", "name", "email", "password", "role"]

    def __init__(self, connection_pool=None):
        super().__init__(connection_pool)
        self.password_hash = None

    def _get_password_hash(self) -> str:
        """Retorna hash da senha padrão (cache)."""
        if self.password_hash is None:
            self.password_hash = RepositoryUtils.hash_password(DEFAULT_PASSWORD)
        return self.password_hash

    @staticmethod
    def _generate_student_name(enrollment: str) -> str:
        """Gera nome realista para estudante baseado na matrícula."""
        return f"Estudante {enrollment}"

    @staticmethod
    def _generate_employee_name(enrollment: str) -> str:
        """Gera nome realista para funcionário baseado no código."""
        codigo = enrollment.replace("FUNC-", "")
        return f"Funcionário {codigo}"

    def _check_user_exists(self, cpf: str) -> bool:
        """Verifica se usuário já existe pelo CPF."""
        return self._check_exists("users", "cpf", cpf)

    def _insert_user(
        self,
        role: str,
        name: str,
        cpf: str,
        email: str,
        enrollment: str
    ) -> bool:
        """
        Insere um usuário.

        Returns:
            True se inseriu, False se falhou
        """
        query = """
            INSERT INTO users (role, name, cpf, email, password, enrollment)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        params = (
            role,
            name,
            cpf,
            email,
            self._get_password_hash(),
            enrollment
        )
        try:
            self._execute_query(query, params)
            return True
        except Exception as e:
            logger.error(f"Erro ao inserir usuário {cpf}: {e}")
            return False

    def seed(self, **kwargs) -> dict[str, Any]:
        """
        Executa seed de usuários.

        Returns:
            Dict com resumo da execução
        """
        self.reset_counts()
        logger.info("Iniciando seed de usuários...")

        # Seed de estudantes
        logger.info("Seed de estudantes...")
        for student_data in STUDENTS_DATA:
            cpf = student_data["cpf"]
            enrollment = student_data["enrollment"]

            # Verifica idempotência
            if self._check_user_exists(cpf):
                self.skipped_count += 1
                logger.debug(f"Estudante {cpf} já existe - pulado")
                continue

            # Gera dados
            name = self._generate_student_name(enrollment)
            email = f"estudante{enrollment}@ufrpe.br"

            # Insere
            if self._insert_user("estudante", name, cpf, email, enrollment):
                self.inserted_count += 1
                logger.debug(f"Estudante {cpf} inserido com sucesso")
            else:
                self.error_count += 1

        # Seed de funcionários
        logger.info("Seed de funcionários...")
        for employee_data in EMPLOYEES_DATA:
            cpf = employee_data["cpf"]
            enrollment = employee_data["enrollment"]

            # Verifica idempotência
            if self._check_user_exists(cpf):
                self.skipped_count += 1
                logger.debug(f"Funcionário {cpf} já existe - pulado")
                continue

            # Gera dados
            name = self._generate_employee_name(enrollment)
            email = f"funcionario{enrollment.replace('FUNC-', '')}@ufrpe.br"

            # Insere
            if self._insert_user("funcionario", name, cpf, email, enrollment):
                self.inserted_count += 1
                logger.debug(f"Funcionário {cpf} inserido com sucesso")
            else:
                self.error_count += 1

        summary = self.get_summary()
        logger.info(
            f"Seed de usuários finalizado: "
            f"{summary['inserted']} inseridos, "
            f"{summary['skipped']} pulados, "
            f"{summary['errors']} erros"
        )

        return {
            "seed_name": self.seed_name,
            "success": True,
            **summary
        }
