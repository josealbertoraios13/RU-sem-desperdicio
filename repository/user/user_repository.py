from datetime import datetime

from repository.repository import Repository
from repository.user.password_reset_token_repository import PasswordResetTokenRepository
from utils import RepositoryUtils, logger
from utils.email.email_service import EmailService


class UserRepository(Repository):
    PART = "user_repository"

    def __init__(self):
        super().__init__()
        self.token_repository = PasswordResetTokenRepository()

    def register_user(self, role: str, name: str, cpf: str, email: str, password: str, enrollment: str, date: datetime) -> dict:
        try:
            hashed_password = RepositoryUtils.hash_password(password)

            error_message = self._check_user_exists(cpf, email, enrollment)
            if error_message:
                return self.build_response(router="register", msg=error_message, success=False,code=409)

            with self.get_connect() as conn:
                with conn.cursor() as cursor:
                    sql_query = """INSERT INTO users
                    (role, name, cpf, email, password, enrollment, register_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)"""

                    cursor.execute(sql_query, (role, name, cpf, email, hashed_password, enrollment, date))

                    return self.build_response(
                        router="register",
                        msg=f"Sucesso: Cadastro de {role} realizado!"
                    )

        except Exception as exception:
            logger.error(f"Error in register_user: {exception}")
            return self.build_response(
                router="register", msg=f"Erro inesperado: {exception}", success=False, code=500
            )

    def login(self, cpf: str, password: str) -> dict:
        try:
            with self.get_connect() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT role, name, email, password, enrollment, register_date FROM users WHERE cpf = %s",
                        (cpf,)
                    )
                    user = cursor.fetchone()
                    if user and RepositoryUtils.verify_password(password, user[3]):
                        role, nome, email, _, enrollment, register_date = user

                        return self.build_response(
                            router="login", msg="Login realizado com sucesso",
                            data=(role, nome, email, cpf, enrollment, register_date)
                        )

                    return self.build_response(
                        router="login",
                        msg="CPF ou senha incorreto ou inexistentes", success=False, code=401
                    )

        except Exception as exception:
            logger.error(f"Error in login: {exception}")
            return self.build_response(
                router="login", msg=f"Erro inesperado: {exception}", success=False, code=500
            )

    def delete_user(self, cpf: str) -> dict:
        try:
            with self.get_connect() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("DELETE FROM users WHERE cpf = %s", (cpf,))
                    deleted_count = cursor.rowcount

                    if deleted_count > 0:
                        return self.build_response(
                            router="delete",
                            msg=f"Sucesso: {deleted_count} usuário(s) excluído(s)"
                        )

                    return self.build_response(
                        router="delete",
                        msg="Erro: Nenhum usuário encontrado com os critérios fornecidos", success=False, code=404
                        )

        except Exception as exception:
            logger.error(f"Error in delete_user: {exception}")
            return self.build_response(
                router="delete", msg=f"Erro inesperado: {exception}", success=False, code=500
            )

    def update_user_password(self, cpf: str, current: str, new: str) -> dict:
        try:
            with self.get_connect() as conn, conn.cursor() as cursor:

                cursor.execute("SELECT password FROM users WHERE cpf = %s", (cpf,))
                user = cursor.fetchone()

                if user:
                    password_hashed = user[0]

                    if not RepositoryUtils.verify_password(current, password_hashed):
                        return self.build_response(
                            router="update_user_password",
                            msg="Erro: Senha atual incorreta!", success=False, code=401
                        )

                    new_password_hashed = RepositoryUtils.hash_password(new)
                    cursor.execute(
                        "UPDATE users SET password = %s WHERE cpf = %s",
                        (new_password_hashed, cpf)
                    )
                    return self.build_response(
                        router="update_user_password",
                        msg="Senha do usuário atualizada com sucesso"
                    )

                return self.build_response(
                    router="update_user_password",
                    msg="Erro: usuário inexistente", success=False, code=404
                )
        except Exception as exception:
            logger.error(f"Error in update_user_password: {exception}")
            return self.build_response(
                router="update_user_password",
                msg=f"Erro inesperado: {exception}", success=False, code=500
            )

    def get_users(self) -> dict:
        try:
            with self.get_connect() as conn, conn.cursor() as cursor:
                cursor.execute(
                    "SELECT role, name, email, enrollment, register_date FROM users ORDER BY name"
                )
                users = cursor.fetchall()

                if users:
                    return self.build_response(
                        router="get_users",
                        msg="Usuários encontrados com sucesso", data=users
                    )

                return self.build_response(
                    router="get_users",
                    msg="Nenhum usuário existente", success=False, code=404
                )

        except Exception as exception:
            logger.error(f"Error in get_users: {exception}")
            return self.build_response(
                router="get_users",
                msg=f"Erro inesperado: {exception}", success=False, code=500
            )

    def password_recover(self, cpf: str, email: str) -> dict:
        try:
            with self.get_connect() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT name, email FROM users WHERE cpf = %s",
                        (cpf,)
                    )
                    user = cursor.fetchone()

                    if not user:
                        return self.build_response(
                            router="password_recover",
                            msg="Erro: não foi possível processar sua solicitação.", success=False, code=400
                        )

                    user_name, registered_email = user

                    if registered_email != email:
                        return self.build_response(
                            router="password_recover",
                            msg="Erro: não foi possível processar sua solicitação.", success=False, code=400
                        )

                    reset_token = self.token_repository.create_token(user_cpf=cpf)

                    email_sent = EmailService.send_password_reset_email(
                        to_email=email,
                        reset_token=reset_token,
                        user_name=user_name
                    )

                    if not email_sent:
                        logger.error("Failed to send password recovery email")
                        return self.build_response(
                            router="password_recover",
                            msg="Erro ao enviar email de recuperação", success=False, code=500
                        )

                    return self.build_response(
                        router="password_recover",
                        msg="Sucesso: instruções de recuperação enviadas para o email."
                    )

        except Exception as exception:
            logger.error(f"Error in password_recover: {exception}")

            return self.build_response(
                router="password_recover",
                msg=f"Erro inesperado: {exception}", success=False, code=500
            )

    def reset_password_with_token(self, token: str, new_password: str) -> dict:
        token_validation = self.token_repository.validate_token(token)

        if not token_validation.get("valid"):
            return self.build_response(
                router="reset_password",
                msg="Token inválido ou expirado", success=False, code=400
            )

        user_cpf = token_validation["user_cpf"]

        hashed_password = RepositoryUtils.hash_password(new_password)

        try:
            with self.get_connect() as conn, conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE users SET password = %s WHERE cpf = %s",
                    (hashed_password, user_cpf)
                )

                if cursor.rowcount == 0:
                    return self.build_response(
                        router="reset_password",
                        msg="Usuário não encontrado", success=False, code=404
                    )

                self.token_repository.mark_token_as_used(token)

                return self.build_response(
                    router="reset_password",
                    msg="Senha redefinida com sucesso!"
                )

        except Exception as exception:
            logger.error(f"Error in reset_password_with_token: {exception}")

            return self.build_response(
                router="reset_password",
                msg=f"Erro inesperado: {exception}", success=False, code=500
            )

    def get_user_by_cpf(self, cpf: str) -> dict:
        try:
            with self.get_connect() as conn, conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, name, cpf, email FROM users WHERE cpf = %s",
                    (cpf,)
                )
                result = cursor.fetchone()

                if result:
                    columns = [desc[0] for desc in cursor.description]
                    return dict(zip(columns, result))

                return self.build_response(
                    router="get_user_by_cpf",
                    msg="Usuário não encontrado ou inexistente",  success=False, code=404
                )
        except Exception as exception:
            logger.error(f"Error in get_user_by_cpf: {exception}")
            return self.build_response(
                router="get_user_by_cpf",
                msg=f"Erro inesperado: {exception}"
            )

    def _check_user_exists(self, cpf: str, email: str, enrollment: str) -> str | None:
        with self.get_connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT cpf, email, enrollment FROM users WHERE cpf = %s OR email = %s OR enrollment = %s",
                    (cpf, email, enrollment,))
                if cursor.fetchone():
                    return "Erro: Este CPF, Email ou Matrícula/Cod. de funcionário já está cadastrado."

        return None
