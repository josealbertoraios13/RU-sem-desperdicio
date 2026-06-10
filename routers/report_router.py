from fastapi import APIRouter, Query, Response

from services import ReportServices

router = APIRouter()
report_services = ReportServices()

@router.get("/reports/demand")
def get_demand(date : str = Query(...)) -> dict:
    return report_services.get_demand(date=date)

@router.get("/reports/export")
def export(date : str = Query(...)) -> Response:
    csv_content, filename = report_services.export_csv(date=date)

    return Response(
        content=csv_content.encode("utf-8-sig"),
        media_type="text/csv",
        headers={
            "Content-Disposition" : f'attachment; filename="{filename}"'
        }
    )

