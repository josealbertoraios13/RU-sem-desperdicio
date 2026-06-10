import hashlib
import secrets
from datetime import datetime, timedelta

from utils.util import Util


class TokenUtils(Util):

    @staticmethod
    def generate_reset_token() -> str:
        return secrets.token_urlsafe(32)

    @staticmethod
    def hash_token(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    def tokens_match(stored_token: str, provided_token: str) -> bool:
        provided_hash = TokenUtils.hash_token(provided_token)
        return secrets.compare_digest(stored_token, provided_hash)

    @staticmethod
    def is_token_expired(created_at: datetime, expiration_hours: int = 1) -> bool:
        expiration_time = created_at + timedelta(hours=expiration_hours)
        return datetime.now() > expiration_time

    @staticmethod
    def get_token_expiry_info(created_at: datetime, expiration_hours: int = 1) -> dict:
        expiration_time = created_at + timedelta(hours=expiration_hours)
        now = datetime.now()
        time_remaining = expiration_time - now

        return {
            "expired": now > expiration_time,
            "expires_at": expiration_time,
            "time_remaining_seconds": max(0, time_remaining.total_seconds()),
            "expiration_hours": expiration_hours
        }
