"""
Push notification channel using Firebase Cloud Messaging (FCM).

Supports two authentication modes:
1. Legacy HTTP API  — uses FCM_SERVER_KEY env var (no extra dependencies)
2. HTTP v1 API      — uses FCM_CREDENTIALS_PATH env var (requires google-auth)

Falls back gracefully if FCM is not configured.
"""
import json
import os

from smartru.notification.channels.base import NotificationChannel
from smartru.utils import logger


class PushChannel(NotificationChannel):
    """
    FCM push notification channel.

    Environment variables:
    - FCM_SERVER_KEY: Legacy FCM server key (from Firebase Console)
    - FCM_CREDENTIALS_PATH: Path to GCP service account JSON for HTTP v1 API
    """

    def __init__(self):
        self._server_key = os.getenv("FCM_SERVER_KEY")
        self._credentials_path = os.getenv("FCM_CREDENTIALS_PATH")
        self._project_id = self._load_project_id()

        if not self._server_key and not self._credentials_path:
            logger.warning(
                "FCM not configured (FCM_SERVER_KEY or FCM_CREDENTIALS_PATH). "
                "Push notifications will be disabled."
            )

    def _load_project_id(self) -> str | None:
        if not self._credentials_path:
            return None
        try:
            with open(self._credentials_path) as f:
                creds = json.load(f)
            project_id = creds.get("project_id")
            logger.info(f"FCM HTTP v1 API configured for project: {project_id}")
            return project_id
        except Exception as e:
            logger.error(f"Failed to load FCM credentials file: {e}")
            return None

    def _is_configured(self) -> bool:
        return bool(self._server_key or self._credentials_path)

    def send(
        self,
        user_cpf: str,
        title: str,
        message: str,
        device_token: str | None = None,
        **kwargs,
    ) -> dict:
        """
        Send a push notification via FCM.

        Args:
            user_cpf: User identifier (for logging)
            title: Notification title
            message: Notification body
            device_token: FCM device registration token

        Returns:
            dict with keys: success, error_message, needs_token_deactivation
        """
        if not self._is_configured():
            return {
                "success": False,
                "error_message": "FCM not configured",
                "needs_token_deactivation": False,
            }

        if not device_token:
            return {
                "success": False,
                "error_message": "No device token provided",
                "needs_token_deactivation": False,
            }

        # Prefer HTTP v1 API if credentials are available
        if self._credentials_path and self._project_id:
            return self._send_v1(device_token, title, message)

        # Fallback to legacy API
        return self._send_legacy(device_token, title, message)

    def _send_v1(self, device_token: str, title: str, message: str) -> dict:
        """Send via FCM HTTP v1 API (requires google-auth)."""
        import http.client
        import ssl

        access_token = self._get_access_token()
        if not access_token:
            return {
                "success": False,
                "error_message": "Failed to obtain FCM access token",
                "needs_token_deactivation": False,
            }

        payload = {
            "message": {
                "token": device_token,
                "notification": {"title": title, "body": message},
                "android": {
                    "priority": "high",
                    "notification": {
                        "channel_id": "smartru_daily_reminder",
                        "click_action": "OPEN_MAIN_ACTIVITY",
                    },
                },
                "data": {"type": "daily_reminder", "screen": "schedule"},
            }
        }

        try:
            conn = http.client.HTTPSConnection(
                "fcm.googleapis.com", context=ssl.create_default_context()
            )
            conn.request(
                "POST",
                f"/v1/projects/{self._project_id}/messages:send",
                json.dumps(payload),
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
            )
            response = conn.getresponse()
            response_body = response.read().decode()
            conn.close()

            if response.status == 200:
                return {
                    "success": True,
                    "error_message": None,
                    "needs_token_deactivation": False,
                }

            error_data = json.loads(response_body)
            error_code = error_data.get("error", {}).get("status", "")
            needs_deactivation = error_code in ("UNREGISTERED", "INVALID_ARGUMENT")

            if needs_deactivation:
                logger.warning(
                    f"FCM token invalid (v1 API): {error_code}"
                )

            return {
                "success": False,
                "error_message": f"FCM v1 error {response.status}: {error_code}",
                "needs_token_deactivation": needs_deactivation,
            }

        except Exception as e:
            logger.error(f"FCM v1 API send failed: {e}")
            return {
                "success": False,
                "error_message": str(e),
                "needs_token_deactivation": False,
            }

    def _get_access_token(self) -> str | None:
        """Obtain OAuth2 access token from service account credentials."""
        try:
            import google.auth.transport.requests
            from google.oauth2 import service_account

            credentials = service_account.Credentials.from_service_account_file(
                self._credentials_path,
                scopes=["https://www.googleapis.com/auth/firebase.messaging"],
            )
            request = google.auth.transport.requests.Request()
            credentials.refresh(request)
            return credentials.token
        except ImportError:
            logger.error(
                "google-auth not installed. Cannot use FCM HTTP v1 API. "
                "Install with: pip install google-auth"
            )
            return None
        except Exception as e:
            logger.error(f"Failed to obtain FCM access token: {e}")
            return None

    def _send_legacy(self, device_token: str, title: str, message: str) -> dict:
        """Send via FCM Legacy HTTP API (server key based)."""
        import http.client
        import ssl

        payload = {
            "to": device_token,
            "notification": {"title": title, "body": message},
            "data": {
                "type": "daily_reminder",
                "screen": "schedule",
            },
            "priority": "high",
        }

        try:
            conn = http.client.HTTPSConnection(
                "fcm.googleapis.com", context=ssl.create_default_context()
            )
            conn.request(
                "POST",
                "/fcm/send",
                json.dumps(payload),
                headers={
                    "Authorization": f"key={self._server_key}",
                    "Content-Type": "application/json",
                },
            )
            response = conn.getresponse()
            response_body = json.loads(response.read().decode())
            conn.close()

            if response.status == 200 and response_body.get("success", 0) == 1:
                return {
                    "success": True,
                    "error_message": None,
                    "needs_token_deactivation": False,
                }

            # Check for invalid/unregistered token
            results = response_body.get("results", [{}])
            error = results[0].get("error", "Unknown") if results else "Unknown"
            needs_deactivation = error in ("NotRegistered", "InvalidRegistration")

            if needs_deactivation:
                logger.warning(f"FCM token invalid (legacy): {error}")

            return {
                "success": False,
                "error_message": f"FCM legacy error: {error}",
                "needs_token_deactivation": needs_deactivation,
            }

        except Exception as e:
            logger.error(f"FCM legacy send failed: {e}")
            return {
                "success": False,
                "error_message": str(e),
                "needs_token_deactivation": False,
            }
