from app.schemas.telemetry import EndpointTelemetryRequest, TelemetryAcceptedResponse
from app.utils.logging import get_logger

logger = get_logger(__name__)


class TelemetryService:
    def accept(self, telemetry: EndpointTelemetryRequest) -> TelemetryAcceptedResponse:
        logger.info(
            "Endpoint telemetry received | agent_id=%s hostname=%s username=%s "
            "cpu=%.2f memory=%.2f processes=%s tcp_connections=%s timestamp=%s",
            telemetry.agent_id,
            telemetry.hostname,
            telemetry.username,
            telemetry.cpu_usage_percent,
            telemetry.memory_usage_percent,
            len(telemetry.running_processes),
            len(telemetry.active_tcp_connections),
            telemetry.timestamp.isoformat(),
        )
        return TelemetryAcceptedResponse()

