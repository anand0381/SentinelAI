from dataclasses import dataclass, field
from datetime import datetime

from app.models.threat import ThreatSeverity


@dataclass(frozen=True)
class DetectionRuleMatch:
    rule_id: str
    name: str
    severity: ThreatSeverity
    reason: str
    creates_threat: bool = True
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class DetectionResult:
    triggered_rules: list[DetectionRuleMatch]
    severity: ThreatSeverity | None
    title: str | None
    description: str | None
    should_create_threat: bool

    @property
    def rule_set_key(self) -> str:
        return ",".join(sorted(rule.rule_id for rule in self.triggered_rules))

