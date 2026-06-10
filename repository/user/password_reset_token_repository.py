from datetime import datetime, timedelta

from repository.repository import Repository
from utils import logger
from utils.security.token_utils import TokenUtils


class PasswordResetTokenRepository(Repository):
    PART = "password_reset_token_repository"

    def create_token(self, user_cpf: str, expiration_hours: int = 1) -> str:
        try:
            plain_token = TokenUtils.generate_reset_token()
            token_hash = TokenUtils.hash_token(plain_token)
            expires_at = datetime.now() + timedelta(hours=expiration_hours)

            with self.get_connect() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "UPDATE password_reset_tokens SET used = TRUE WHERE user_cpf = %s AND used = FALSE",
                        (user_cpf,)
                    )

                    cursor.execute(
                        """INSERT INTO password_reset_tokens
                           (user_cpf, token_hash, expires_at)
                           VALUES (%s, %s, %s)""",
                        (user_cpf, token_hash, expires_at)
                    )

            logger.info(f"Password reset token created for CPF: {user_cpf[:3]}***")
            return plain_token

        except Exception as exception:
            logger.error(f"Error creating password reset token: {exception}")
            raise exception

    def validate_token(self, token: str) -> dict:
        try:
            token_hash = TokenUtils.hash_token(token)

            with self.get_connect() as conn, conn.cursor() as cursor:
                cursor.execute(
                    """SELECT user_cpf, created_at, expires_at, used
                           FROM password_reset_tokens
                           WHERE token_hash = %s""",
                    (token_hash,)
                )
                result = cursor.fetchone()

                if not result:
                    return {
                        "valid": False,
                        "reason": "Token inválido ou não encontrado"
                    }

                user_cpf, created_at, expires_at, used = result

                if used:
                    return {
                        "valid": False,
                        "reason": "Token já foi utilizado"
                    }

                if datetime.now() > expires_at:
                    return {
                        "valid": False,
                        "reason": "Token expirado"
                    }

                return {
                    "valid": True,
                    "user_cpf": user_cpf,
                    "created_at": created_at,
                    "expires_at": expires_at
                }

        except Exception as exception:
            logger.error(f"Error validating password reset token: {exception}")
            return {
                "valid": False,
                "reason": "Erro interno ao validar token"
            }

    def mark_token_as_used(self, token: str) -> bool:
        try:
            token_hash = TokenUtils.hash_token(token)

            with self.get_connect() as conn, conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE password_reset_tokens SET used = TRUE WHERE token_hash = %s",
                    (token_hash,)
                )
                return cursor.rowcount > 0

        except Exception as exception:
            logger.error(f"Error marking token as used: {exception}")
            return False

    def cleanup_expired_tokens(self) -> int:
        try:
            with self.get_connect() as conn, conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM password_reset_tokens WHERE expires_at < NOW()"
                )
                return cursor.rowcount

        except Exception as exception:
            logger.error(f"Error cleaning up expired tokens: {exception}")
            return 0
