import csv
from io import StringIO

from smartru.repository import ReportRepository
from smartru.services.service import Service
from smartru.utils import ReportUtils


class ReportServices(Service):
    def __init__(self) -> None:
        self.repository = ReportRepository()

    def get_demand(self, date : str) -> dict:
        ReportUtils.validate_date(date=date)

        parsed_date = ReportUtils.parse_date(date=date, format="%d/%m/%Y")

        result = self.repository.get_demand(schedule_date=parsed_date)

        return self.handle_response(response=result)

    def export_csv(self, date : str) -> tuple[str, str]:
        ReportUtils.validate_date(date=date)

        parsed_date = ReportUtils.parse_date(date=date, format="%d/%m/%Y")

        result = self.repository.get_export_data(schedule_date=parsed_date)
        result = self.handle_response(response=result)
        rows = result["data"]

        output = StringIO()
        writer = csv.writer(output)

        writer.writerow(
        ["nome", "cpf", "tipo_refeicao", "data", "horario", "data_criacao"]
        )

        for row in rows:
            writer.writerow([
            row["name"],
            row["user_cpf"],
            row["schedule_type"],
            row["data"].strftime("%d/%m/%Y"),
            row["estimated_time"],
            row["created_at"].strftime("%d/%m/%Y"),
            ])

        filename = f'relatorio-{date.replace("/", "-")}.csv'

        return output.getvalue(), filename
