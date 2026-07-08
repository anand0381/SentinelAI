from app.models.threat import ThreatSeverity
from app.schemas.telemetry import EndpointTelemetryRequest

from .models import DetectionResult, DetectionRuleMatch


class DetectionEvaluator:
    severity_rank = {
        ThreatSeverity.LOW: 1,
        ThreatSeverity.MEDIUM: 2,
        ThreatSeverity.HIGH: 3,
        ThreatSeverity.CRITICAL: 4,
    }

    def evaluate(
        self,
        telemetry: EndpointTelemetryRequest,
        matches: list[DetectionRuleMatch],
    ) -> DetectionResult:
        threat_rules = [rule for rule in matches if rule.creates_threat]
        if not threat_rules:
            return DetectionResult(
                triggered_rules=matches,
                severity=None,
                title=None,
                description=None,
                should_create_threat=False,
            )

        severity = self._calculate_severity(matches)
        return DetectionResult(
            triggered_rules=matches,
            severity=severity,
            title="Suspicious Endpoint Activity Detected",
            description=self._build_description(telemetry, matches, severity),
            should_create_threat=True,
        )

    def _calculate_severity(
        self,
        matches: list[DetectionRuleMatch],
    ) -> ThreatSeverity:
        if len(matches) > 1:
            return ThreatSeverity.CRITICAL

        return max(matches, key=lambda item: self.severity_rank[item.severity]).severity

    def _build_description(
        self,
        telemetry: EndpointTelemetryRequest,
        matches: list[DetectionRuleMatch],
        severity: ThreatSeverity,
    ) -> str:
        suspicious_processes = self._suspicious_processes(matches)
        rule_names = ", ".join(rule.name for rule in matches)
        rule_set_key = ",".join(sorted(rule.rule_id for rule in matches))

        return (
            "Endpoint telemetry triggered SentinelAI detection rules.\n\n"
            f"Detection Hostname: {telemetry.hostname}\n"
            f"Detection Username: {telemetry.username}\n"
            f"Detection Rule Set: {rule_set_key}\n"
            f"Triggered Rules: {rule_names}\n"
            f"Calculated Severity: {severity.value}\n"
            f"CPU Usage: {telemetry.cpu_usage_percent:.2f}%\n"
            f"Memory Usage: {telemetry.memory_usage_percent:.2f}%\n"
            f"TCP Connections: {len(telemetry.active_tcp_connections)}\n"
            f"Suspicious Processes: {', '.join(suspicious_processes) or 'None'}\n"
            f"Telemetry Timestamp: {telemetry.timestamp.isoformat()}\n"
        )

    def _suspicious_processes(self, matches: list[DetectionRuleMatch]) -> list[str]:
        processes: list[str] = []
        for match in matches:
            match_processes = match.metadata.get("processes", [])
            if isinstance(match_processes, list):
                processes.extend(str(process) for process in match_processes)
        return sorted(set(processes))

