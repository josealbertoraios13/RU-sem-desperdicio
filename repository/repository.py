import os
from contextlib import contextmanager

from dotenv import load_dotenv
from psycopg2 import pool

from smartru.paths import PROJECT_ROOT, SCHEMA_SQL
from smartru.utils import logger

load_dotenv(PROJECT_ROOT / ".env")


class Repository:
    _connection_pool = None
    _schema_initialized = False

    PART = "Repository"

    def __init__(self):
        self.schema_file = str(SCHEMA_SQL)
        # Connection pool is lazily initialized on first use

    def _ensure_pool(self) -> None:
        """Lazy-initialize the connection pool on first use."""
        if Repository._connection_pool is None:
            self._init_connection_pool()
        self.connection_pool = Repository._connection_pool

    def _init_connection_pool(self) -> None:
        try:
            # Atribui ao atributo de classe
            Repository._connection_pool = pool.ThreadedConnectionPool(
                minconn=int(os.getenv('DB_POOL_MIN_CONNECTIONS', 1)),
                maxconn=int(os.getenv('DB_POOL_MAX_CONNECTIONS', 20)),
                host=os.getenv('POSTGRES_HOST'),
                port=os.getenv('POSTGRES_PORT'),
                database=os.getenv('POSTGRES_DB'),
                user=os.getenv('POSTGRES_USER'),
                password=os.getenv('POSTGRES_PASSWORD'),
                connect_timeout=int(os.getenv('DB_POOL_TIMEOUT', 30))
            )
            logger.info("Conexão PostgreSQL inicializada com sucesso!")
            # Ensure base schema is present for fresh databases before any repository operation.
            if not Repository._schema_initialized:
                self.initialize_database()
                Repository._schema_initialized = True
                logger.info("Schema do banco inicializado/verificado com sucesso.")
        except Exception as e:
            logger.error(f"Falha na inicialização da conexão com PostgreSQL: {e}")
            raise

    def connect(self):
        self._ensure_pool()

        try:
            conn = Repository._connection_pool.getconn()
            return conn
        except Exception as e:
            logger.error(f"Tentativa de conexão falha: {e}")
            raise

    @contextmanager
    def get_connect(self):
        conn = self.connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            if Repository._connection_pool is None:
                logger.error("Pool de conexões não inicializado.")
                raise Exception("Database pool is not initialized")

            Repository._connection_pool.putconn(conn)

    def initialize_database(self) -> None:
        try:
            if os.path.exists(self.schema_file):
                with open(self.schema_file, encoding='utf-8') as file:
                    schema_script = file.read()

                with self.get_connect() as conn, conn.cursor() as cursor:
                    cursor.execute(schema_script)
            else:
                logger.error(f"Schema file not found: {self.schema_file}")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def build_response(self, router: str, msg: str, success: bool = True, code : int | None = None, data=None) -> dict:
        response = {
            "success": success,
            "router": router,
            "part": self.PART,
            "msg": msg
        }

        if code is not None:
            response["code"] = code

        if data is not None:
            response["data"] = data
        return response
