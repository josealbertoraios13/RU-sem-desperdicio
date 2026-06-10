from abc import ABC, abstractmethod


class NotificationChannel(ABC):
    """Abstract base for all notification delivery channels."""

    @abstractmethod
    def send(self, user_cpf: str, title: str, message: str, **kwargs) -> dict:
        """
        Send a notification through this channel.

        Returns:
            dict with keys:
                - success (bool): Whether the send was successful
                - error_message (str | None): Error description if failed
                - needs_token_deactivation (bool, optional): If True, the
                  device token should be deactivated (push-specific)
        """
        ...
