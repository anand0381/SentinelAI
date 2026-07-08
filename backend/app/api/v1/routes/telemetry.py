from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
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
    db: Annotated[Session, Depends(get_db)],
) -> TelemetryAcceptedResponse:
    return TelemetryService(db).accept(telemetry)
