from app.config.settings import Settings
from app.models.threat import ThreatSeverity
from app.schemas.telemetry import EndpointTelemetryRequest

from .models import DetectionRuleMatch


class DetectionRules:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def evaluate(self, telemetry: EndpointTelemetryRequest) -> list[DetectionRuleMatch]:
        matches: list[DetectionRuleMatch] = []
        matches.extend(self._high_cpu(telemetry))
        matches.extend(self._high_memory(telemetry))
        matches.extend(self._large_tcp_connection_count(telemetry))
        matches.extend(self._suspicious_processes(telemetry))
        return matches

    def _high_cpu(
        self,
        telemetry: EndpointTelemetryRequest,
    ) -> list[DetectionRuleMatch]:
        if telemetry.cpu_usage_percent < self.settings.detection_cpu_threshold:
            return []

        return [
            DetectionRuleMatch(
                rule_id="HIGH_CPU",
                name="High CPU",
                severity=ThreatSeverity.HIGH,
                reason="Possible malware, cryptomining or resource abuse.",
                metadata={"cpu_usage_percent": telemetry.cpu_usage_percent},
            )
        ]

    def _high_memory(
        self,
        telemetry: EndpointTelemetryRequest,
    ) -> list[DetectionRuleMatch]:
        if telemetry.memory_usage_percent < self.settings.detection_memory_threshold:
            return []

        return [
            DetectionRuleMatch(
                rule_id="HIGH_MEMORY",
                name="High Memory",
                severity=ThreatSeverity.HIGH,
                reason="Possible memory abuse or unstable endpoint activity.",
                metadata={"memory_usage_percent": telemetry.memory_usage_percent},
            )
        ]

    def _large_tcp_connection_count(
        self,
        telemetry: EndpointTelemetryRequest,
    ) -> list[DetectionRuleMatch]:
        tcp_connection_count = len(telemetry.active_tcp_connections)
        if tcp_connection_count <= self.settings.detection_tcp_connection_threshold:
            return []

        return [
            DetectionRuleMatch(
                rule_id="LARGE_TCP_CONNECTION_COUNT",
                name="Large Number of TCP Connections",
                severity=ThreatSeverity.HIGH,
                reason="Possible scanning, malware communication or beaconing.",
                metadata={"tcp_connection_count": tcp_connection_count},
            )
        ]

    def _suspicious_processes(
        self,
        telemetry: EndpointTelemetryRequest,
    ) -> list[DetectionRuleMatch]:
        suspicious_names = self._suspicious_process_names()
        detected_processes = sorted(
            {
                process.name.lower()
                for process in telemetry.running_processes
                if process.name.lower() in suspicious_names
            }
        )
        if not detected_processes:
            return []

        return [
            DetectionRuleMatch(
                rule_id="SUSPICIOUS_PROCESS",
                name="Suspicious Processes",
                severity=ThreatSeverity.MEDIUM,
                reason="Suspicious process execution observed on endpoint.",
                creates_threat=False,
                metadata={"processes": detected_processes},
            )
        ]

    def _suspicious_process_names(self) -> set[str]:
        return {
            item.strip().lower()
            for item in self.settings.detection_suspicious_processes.split(",")
            if item.strip()
        }

