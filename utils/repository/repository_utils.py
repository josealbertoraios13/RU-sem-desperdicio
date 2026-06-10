import bcrypt

from utils.logger import logger


class RepositoryUtils:
    @staticmethod
    def close(connection_pool) -> None:
        try:
            connection_pool.closeall()
            logger.info("Database connection pool closed")
        except Exception as e:
            logger.debug(f"Error closing connection pool: {e}")

    @staticmethod
    def hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        return bcrypt.checkpw(password.encode(), hashed.encode())
