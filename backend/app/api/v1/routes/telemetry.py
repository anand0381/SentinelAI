from fastapi import APIRouter

from app.schemas.telemetry import EndpointTelemetryRequest, TelemetryAcceptedResponse
from app.telemetry.service import TelemetryService

router = APIRouter()


@router.post(
    "",
    response_model=TelemetryAcceptedResponse,
    summary="Receive endpoint telemetry",
)
def receive_telemetry(
    telemetry: EndpointTelemetryRequest,
) -> TelemetryAcceptedResponse:
    return TelemetryService().accept(telemetry)

