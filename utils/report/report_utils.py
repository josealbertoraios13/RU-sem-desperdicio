from datetime import date, datetime

from utils.util import Util


class ReportUtils(Util):

    @staticmethod
    def _is_valid_date(date: str) -> bool:
        try:
            datetime.strptime(date, "%d/%m/%Y")
            return True
        except ValueError:
            return False

    @staticmethod
    def validate_date(date: str) -> None:
        if not ReportUtils._is_valid_date(date=date):
            Util.return_http_exception(message="Data inválida. Use o formato DD/MM/YYYY.")

    @staticmethod
    def parse_date(date: str, format: str) -> date:
        try:
            return datetime.strptime(date, format).date()
        except ValueError:
            Util.return_http_exception(message=f"Data inválida. Use o formato {format}.")
            raise  # mypy needs this to know the function doesn't fall through
