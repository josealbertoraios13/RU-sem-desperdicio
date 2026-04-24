import psycopg2
from psycopg2 import pool
import bcrypt
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    filename="app.log",
    filemode="a",
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataBase:
    def __init__(self):
        self.schema_file = "database/schema.sql"
        self._init_connection_pool()

    def _init_connection_pool(self):
        """Initialize PostgreSQL connection pool"""
        try:
            self.connection_pool = pool.ThreadedConnectionPool(
                minconn=int(os.getenv('DB_POOL_MIN_CONNECTIONS', 1)),
                maxconn=int(os.getenv('DB_POOL_MAX_CONNECTIONS', 20)),
                host=os.getenv('POSTGRES_HOST', 'localhost'),
                port=os.getenv('POSTGRES_PORT', '5432'),
                database=os.getenv('POSTGRES_DB', 'smartru_db'),
                user=os.getenv('POSTGRES_USER', 'smartru_user'),
                password=os.getenv('POSTGRES_PASSWORD', 'smartru_password'),
                connect_timeout=int(os.getenv('DB_POOL_TIMEOUT', 30))
            )
            logger.info("PostgreSQL connection pool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise

    def connect(self):
        """Get a connection from the pool"""
        try:
            conn = self.connection_pool.getconn()
            return conn
        except Exception as e:
            logger.error(f"Failed to get connection from pool: {e}")
            raise

    def initialize_database(self):
        """Initialize database schema if not exists"""
        try:
            if os.path.exists(self.schema_file):
                with open(self.schema_file, 'r', encoding='utf-8') as file:
                    schema_script = file.read()

                conn = self.connect()
                try:
                    with conn.cursor() as cursor:
                        cursor.execute(schema_script)
                    conn.commit()
                    logger.info("Database schema initialized successfully")
                finally:
                    self.connection_pool.putconn(conn)
            else:
                logger.error(f"Schema file not found: {self.schema_file}")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def register_user(self, user_type, name, cpf, email, password, enrollment=None, employee_code=None):
        error_msg = self._check_user_exists(cpf, email, enrollment, employee_code)
        if error_msg:
            return error_msg
        
        hashed_password = self._hash_password(password)

        try:
            conn = self.connect()
            try:
                with conn.cursor() as cursor:
                    sql_query = """INSERT INTO usuarios
                             (tipo_usuario, nome_completo, cpf, email, senha, matricula, codigo_funcionario)
                             VALUES (%s, %s, %s, %s, %s, %s, %s)"""

                    cursor.execute(sql_query, (user_type, name, cpf, email, hashed_password.decode('utf-8'), enrollment, employee_code))
                    conn.commit()

                    return f"Sucesso: Cadastro de {user_type} realizado!"
            finally:
                self.connection_pool.putconn(conn)

        except psycopg2.IntegrityError as e:
            if "usuarios_cpf_key" in str(e):
                return "Erro: Este CPF já está cadastrado."
            elif "usuarios_email_key" in str(e):
                return "Erro: Este Email já está cadastrado."
            elif "usuarios_matricula_key" in str(e):
                return "Erro: Esta Matrícula já está cadastrada."
            elif "usuarios_codigo_funcionario_key" in str(e):
                return "Erro: Este Código de Funcionário já está cadastrado."
            else:
                return f"Erro de integridade: {e}"
        except Exception as exception:
            logger.error(f"Error in register_user: {exception}")
            return f"Erro inesperado: {exception}"
        

    def login(self, cpf, password):
        try:
            conn = self.connect()
            try:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT id, nome_completo, email, tipo_usuario, senha, matricula, codigo_funcionario FROM usuarios WHERE cpf = %s",
                        (cpf,)
                    )
                    user = cursor.fetchone()

                    if user:
                        user_id, nome, email, tipo, senha_hash, matricula, codigo_funcionario = user

                        if self._verify_password(password, senha_hash.encode('utf-8') if isinstance(senha_hash, str) else senha_hash):
                            return {
                                "success": True,
                                "message": "Login realizado com sucesso",
                                "data": (user_id, nome, tipo, email, cpf, matricula, codigo_funcionario)
                            }

                return {
                    "success": False,
                    "message": "CPF ou senha inválidos",
                    "data": None
                }
            finally:
                self.connection_pool.putconn(conn)

        except Exception as e:
            logger.error(f"Error in login: {e}")
            return {
                "success": False,
                "message": f"Erro inesperado: {e}",
                "data": None
            }

    def schedule_meal(self, user_id, meal_type, date, time):
        try:
            conn = self.connect()
            try:
                with conn.cursor() as cursor:
                    sql_query = "INSERT INTO agendamentos (usuario_id, tipo_refeicao, data_refeicao, horario_estimado) VALUES (%s, %s, %s, %s)"

                    cursor.execute(sql_query, (user_id, meal_type, date, time))
                    conn.commit()
                    return f"Sucesso: {meal_type.capitalize()} agendado para {date}!"
            finally:
                self.connection_pool.putconn(conn)

        except psycopg2.IntegrityError:
            return "Erro: Você já possui um agendamento para esta refeição nesta data."
        except Exception as e:
            logger.error(f"Error in schedule_meal: {e}")
            return f"Erro inesperado: {e}"
        
    # Utils

    def close(self):
        """Close all connections in the pool"""
        if hasattr(self, 'connection_pool'):
            try:
                self.connection_pool.closeall()
                logger.info("Database connection pool closed")
            except Exception as e:
                logger.debug(f"Error closing connection pool: {e}")

    def __del__(self):
        """Destructor to ensure connections are closed"""
        try:
            self.close()
        except Exception:
            pass  # Ignore errors during garbage collection

    @staticmethod
    def _hash_password(password):
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    @staticmethod
    def _verify_password(password, hashed):
        return bcrypt.checkpw(password.encode(), hashed)
        

    def _check_user_exists(self, cpf, email, enrollment, employee_code):
        """Check if user with given credentials already exists"""
        conn = self.connect()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1 FROM usuarios WHERE cpf = %s", (cpf,))
                if cursor.fetchone():
                    return "Erro: Este CPF já está cadastrado."

                cursor.execute("SELECT 1 FROM usuarios WHERE email = %s", (email,))
                if cursor.fetchone():
                    return "Erro: Este Email já está cadastrado."

                if enrollment:
                    cursor.execute("SELECT 1 FROM usuarios WHERE matricula = %s", (enrollment,))
                    if cursor.fetchone():
                        return "Erro: Esta Matrícula já está cadastrada."

                if employee_code:
                    cursor.execute("SELECT 1 FROM usuarios WHERE codigo_funcionario = %s", (employee_code,))
                    if cursor.fetchone():
                        return "Erro: Este Código de Funcionário já está cadastrado."

            return None
        finally:
            self.connection_pool.putconn(conn)

    def delete_user(self, cpf=None, email=None, user_id=None):
        """Delete a user by CPF, email, or user ID"""
        # Validate that at least one identifier is provided
        if not any([cpf, email, user_id]):
            return "Erro: Pelo menos um identificador (CPF, email ou ID) deve ser fornecido"
        
        conn = self.connect()
        try:
            with conn.cursor() as cursor:
                # Build the WHERE clause based on provided parameters
                conditions = []
                params = []
                
                if cpf is not None:
                    conditions.append("cpf = %s")
                    params.append(cpf)
                if email is not None:
                    conditions.append("email = %s")
                    params.append(email)
                if user_id is not None:
                    conditions.append("id = %s")
                    params.append(user_id)
                
                where_clause = " AND ".join(conditions)
                sql_query = f"DELETE FROM usuarios WHERE {where_clause}"
                
                cursor.execute(sql_query, params)
                deleted_count = cursor.rowcount
                conn.commit()
                
                if deleted_count > 0:
                    return f"Sucesso: {deleted_count} usuário(s) excluído(s)!"
                else:
                    return "Erro: Nenhum usuário encontrado com os critérios fornecidos"
                    
        except Exception as e:
            logger.error(f"Error in delete_user: {e}")
            return f"Erro inesperado: {e}"
        finally:
            self.connection_pool.putconn(conn)

    def delete_schedule(self, user_id, meal_type, date):
        """Delete a specific meal schedule for a user"""
        try:
            conn = self.connect()
            try:
                with conn.cursor() as cursor:
                    sql_query = "DELETE FROM agendamentos WHERE usuario_id = %s AND tipo_refeicao = %s AND data_refeicao = %s"
                    
                    cursor.execute(sql_query, (user_id, meal_type, date))
                    deleted_count = cursor.rowcount
                    conn.commit()
                    
                    if deleted_count > 0:
                        return f"Sucesso: Agendamento de {meal_type} para {date} excluído!"
                    else:
                        return "Erro: Nenhum agendamento encontrado com os critérios fornecidos"
            finally:
                self.connection_pool.putconn(conn)
                
        except Exception as e:
            logger.error(f"Error in delete_schedule: {e}")
            return f"Erro inesperado: {e}"

    def get_meal_history(self, user_id):
        """Get meal scheduling history for a user"""
        try:
            conn = self.connect()
            try:
                with conn.cursor() as cursor:
                    sql_query = """
                        SELECT id, tipo_refeicao, data_refeicao, horario_estimado
                        FROM agendamentos
                        WHERE usuario_id = %s
                        ORDER BY data_refeicao DESC, tipo_refeicao
                    """

                    cursor.execute(sql_query, (user_id,))
                    schedules = cursor.fetchall()

                    return schedules
            finally:
                self.connection_pool.putconn(conn)

        except Exception as e:
            logger.error(f"Error in get_meal_history: {e}")
            return []
        
    def get_all_meal_history(self):
        """Get meal scheduling history for all users"""
        try:
            conn = self.connect()
            try:
                with conn.cursor() as cursor:
                    sql_query = """
                        SELECT id, tipo_refeicao, data_refeicao, horario_estimado
                        FROM agendamentos
                        ORDER BY data_refeicao DESC, tipo_refeicao
                    """

                    cursor.execute(sql_query)
                    schedules = cursor.fetchall()

                    return schedules
            finally:
                self.connection_pool.putconn(conn)

        except Exception as e:
            logger.error(f"Error in get_all_meal_history: {e}")
            return []