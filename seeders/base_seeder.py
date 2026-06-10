"""
Classe base para todos os seeders.

Fornece funcionalidades comuns:
- Idempotência (verifica existência antes de inserir)
- Logs padronizados
- Tratamento de erros
- Suporte a transações
"""

import re
from abc import ABC, abstractmethod
from typing import Any

from psycopg2 import pool

from smartru.utils.logger import logger


class BaseSeeder(ABC):
    """
    Classe base abstrata para seeders.

    Todo seeder deve implementar:
    - seed_name: identificador único
    - required_fields: campos obrigatórios
    - seed(): método principal de execução
    """

    seed_name: str = "base_seeder"
    required_fields: list[str] = []

    def __init__(self, connection_pool: pool.ThreadedConnectionPool | None = None):
        """
        Inicializa o seeder.

        Args:
            connection_pool: Pool de conexões do psycopg2
        """
        self.connection_pool = connection_pool
        self.inserted_count = 0
        self.skipped_count = 0
        self.error_count = 0

    def _get_connection(self):
        """Obtém conexão do pool."""
        if self.connection_pool is None:
            raise Exception("Database pool is not initialized")
        return self.connection_pool.getconn()

    def _release_connection(self, conn):
        """Libera conexão de volta ao pool."""
        if self.connection_pool is not None:
            self.connection_pool.putconn(conn)

    def _execute_query(
        self,
        query: str,
        params: tuple = (),
        fetch: bool = False
    ) -> Any | None:
        """
        Executa query SQL com tratamento de erros.

        Args:
            query: SQL query com placeholders %s
            params: Parâmetros para a query
            fetch: Se True, retorna resultado (fetchone/fetchall)

        Returns:
            Resultado da query se fetch=True, None caso contrário
        """
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                if fetch:
                    result = cursor.fetchall()
                    columns = [desc[0] for desc in cursor.description]
                    return [dict(zip(columns, row)) for row in result]
                conn.commit()
                return None
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Erro em {self.seed_name}: {e}")
            raise
        finally:
            if conn:
                self._release_connection(conn)

    def _execute_many(
        self,
        query: str,
        params_list: list[tuple]
    ) -> int:
        """
        Executa inserção em lote com tratamento de erros.

        Args:
            query: SQL query com placeholders %s
            params_list: Lista de tuplas de parâmetros

        Returns:
            Número de linhas afetadas
        """
        if not params_list:
            return 0

        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.executemany(query, params_list)
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Erro em {self.seed_name} (executemany): {e}")
            raise
        finally:
            if conn:
                self._release_connection(conn)

    def _check_exists(self, table: str, field: str, value: Any) -> bool:
        """
        Verifica se registro já existe na tabela.

        Args:
            table: Nome da tabela
            field: Campo a ser verificado
            value: Valor do campo

        Returns:
            True se existir, False caso contrário
        """
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", table):
            raise ValueError(f"Nome de tabela inválido: {table}")
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", field):
            raise ValueError(f"Nome de campo inválido: {field}")

        query = f"SELECT 1 FROM {table} WHERE {field} = %s LIMIT 1"
        result = self._execute_query(query, (value,), fetch=True)
        return len(result) > 0 if result else False

    def _check_exists_composite(
        self,
        table: str,
        fields: list[str],
        values: list[Any]
    ) -> bool:
        """
        Verifica existência por múltiplos campos (AND).

        Args:
            table: Nome da tabela
            fields: Lista de nomes de campos
            values: Lista de valores correspondentes

        Returns:
            True se existir, False caso contrário
        """
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", table):
            raise ValueError(f"Nome de tabela inválido: {table}")
        for field in fields:
            if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", field):
                raise ValueError(f"Nome de campo inválido: {field}")

        conditions = " AND ".join([f"{f} = %s" for f in fields])
        query = f"SELECT 1 FROM {table} WHERE {conditions} LIMIT 1"
        result = self._execute_query(query, tuple(values), fetch=True)
        return len(result) > 0 if result else False

    def _validate_record(self, record: dict[str, Any]) -> bool:
        """
        Valida se registro possui campos obrigatórios.

        Args:
            record: Dicionário com dados do registro

        Returns:
            True se válido, False caso contrário
        """
        for field in self.required_fields:
            if field not in record or record[field] is None:
                return False
        return True

    @abstractmethod
    def seed(self, **kwargs) -> dict[str, Any]:
        """
        Método principal de execução do seed.

        Returns:
            Dicionário com resultado da execução
        """
        pass

    def reset_counts(self):
        """Reseta contadores para próxima execução."""
        self.inserted_count = 0
        self.skipped_count = 0
        self.error_count = 0

    def get_summary(self) -> dict[str, int]:
        """Ret resumo da execução."""
        return {
            "inserted": self.inserted_count,
            "skipped": self.skipped_count,
            "errors": self.error_count,
            "total": self.inserted_count + self.skipped_count + self.error_count
        }
