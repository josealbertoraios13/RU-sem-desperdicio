import psycopg2
from psycopg2 import pool
import bcrypt
import os
from dotenv import load_dotenv
import logging

# Carrega as váriaveis de ambiente
load_dotenv()

# Configura para onde as mensagens de debug vão ser direcionadas(arquivo app.log)
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
        try:
            self.connection_pool = pool.ThreadedConnectionPool(
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
        except Exception as e:
            logger.error(f"Falha na inicialização da conexão com PostgreSQL: {e}")
            raise

    def connect(self):
        # Faz uma conexão
        try:
            conn = self.connection_pool.getconn()
            return conn
        except Exception as e:
            logger.error(f"Tentativa de conexão falha: {e}")
            raise

    def initialize_database(self):
        # Inicializa o schema.sql do banco de dados caso ele exista
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

    def register_user(
            self, user_type : str, name : str,
            cpf : str, email : str, password : str, 
            enrollment : str | None = None, employee_code : str | None = None
            ) -> str: 
        
        if enrollment is str and employee_code is str:
            error_msg = self._check_user_exists(cpf, email, enrollment , employee_code)
            
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
            
            return f"Erro de integridade: {e}"
        
        except Exception as exception:
            logger.error(f"Error in register_user: {exception}")
            return f"Erro inesperado: {exception}"

    def login(self, cpf : str, password : str) -> dict:
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

    def schedule_meal(self, user_id : str, meal_type : str, date : str, time : str) -> str:
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

    def close(self) -> None:
        # Encerra todas as conexões
        if hasattr(self, 'connection_pool'):
            try:
                self.connection_pool.closeall()
                logger.info("Database connection pool closed")
            except Exception as e:
                logger.debug(f"Error closing connection pool: {e}")

    def __del__(self):
        # Destrutor para garantir que todas as conexões sejam encerradas
        try:
            self.close()
        except Exception:
            pass  # Ignora erros durante o carbage collector

    @staticmethod
    def _hash_password(password : str) -> bytes:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    @staticmethod
    def _verify_password(password : str, hashed : bytes) -> bool:
        return bcrypt.checkpw(password.encode(), hashed)
        

    def _check_user_exists(self, cpf : str, email : str, enrollment : str, employee_code : str) -> str | None:
        # Verifica se o usuário existe usando as credênciais: cpf, email enrollment, employee_code
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

    def delete_user(self, cpf : str | None = None, email : str | None = None, user_id : str | None = None) -> str:
        # Deleta usuário com base no cpf, email ou id

        # Valida se pelo menos um parâmetro da função é válido        
        if not any([cpf, email, user_id]):
            return "Erro: Pelo menos um identificador (CPF, email ou ID) deve ser fornecido"
        
        conn = self.connect()
        try:
            with conn.cursor() as cursor:
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

                return "Erro: Nenhum usuário encontrado com os critérios fornecidos"
                    
        except Exception as e:
            logger.error(f"Error in delete_user: {e}")
            return f"Erro inesperado: {e}"
        finally:
            self.connection_pool.putconn(conn)

    def delete_schedule(self, user_id : str, meal_type : str, date : str) -> str:
        # Deleta um agendamento 
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

                    return "Erro: Nenhum agendamento encontrado com os critérios fornecidos"
            finally:
                self.connection_pool.putconn(conn)
                
        except Exception as e:
            logger.error(f"Error in delete_schedule: {e}")
            return f"Erro inesperado: {e}"

    def get_meal_history(self, user_id : str) -> list:
        # Puxa o histórico de agendamentos do usuário
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
        
    def get_all_meal_history(self) -> list:
        # Puxa todos os agendamentos de todos os usuários
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