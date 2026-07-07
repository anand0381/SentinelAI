import hashlib
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status

from app.ai.gemini_provider import GeminiProvider
from app.ai.metrics import AIMetrics
from app.ai.prompt_builder import ThreatPromptBuilder
from app.ai.response_parser import AIResponseParser, ThreatAIAnalysis
from app.models.threat import Threat
from app.utils.logging import get_logger

logger = get_logger(__name__)


class AIService:
    _analysis_input_fingerprints: dict[int, str] = {}

    def __init__(self) -> None:
        self.prompt_builder = ThreatPromptBuilder()
        self.provider = GeminiProvider()
        self.response_parser = AIResponseParser()

    def analyze_threat(self, threat: Threat, force: bool = False) -> ThreatAIAnalysis:
        prompt = self.prompt_builder.build(threat)
        input_fingerprint = self._fingerprint(prompt)

        if not force:
            cached_analysis = self._get_cached_analysis(threat, input_fingerprint)
            if cached_analysis is not None:
                logger.info(
                    "AI cache hit - existing analysis returned. threat_id=%s",
                    threat.id,
                )
                AIMetrics.record_cache_hit()
                return cached_analysis

        AIMetrics.record_cache_miss()
        logger.info("AI cache miss. threat_id=%s force=%s", threat.id, force)
        raw_response = self.provider.generate_json(prompt, threat_id=threat.id)

        try:
            analysis = self.response_parser.parse(raw_response)
        except ValueError as exc:
            logger.warning(
                "AI response parsing failed once for threat_id=%s: %s",
                threat.id,
                exc,
            )
            raw_response = self.provider.generate_json(prompt, threat_id=threat.id)
            try:
                analysis = self.response_parser.parse(raw_response)
            except ValueError as retry_exc:
                logger.exception(
                    "AI response parsing failed after retry for threat_id=%s",
                    threat.id,
                )
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="AI analysis is temporarily unavailable.",
                ) from retry_exc

        self._analysis_input_fingerprints[threat.id] = input_fingerprint
        return analysis

    def apply_analysis(self, threat: Threat, analysis: ThreatAIAnalysis) -> None:
        threat.ai_summary = analysis.ai_summary
        threat.attack_vector = analysis.attack_vector
        threat.business_impact = analysis.business_impact
        threat.mitre_attack = analysis.mitre_attack
        threat.recommendations = analysis.recommendations
        threat.confidence_score = analysis.confidence_score
        threat.risk_score = analysis.risk_score
        threat.last_analyzed = datetime.now(timezone.utc)

    def _get_cached_analysis(
        self,
        threat: Threat,
        input_fingerprint: str,
    ) -> ThreatAIAnalysis | None:
        if not self._has_completed_analysis(threat):
            return None

        stored_fingerprint = self._analysis_input_fingerprints.get(threat.id)
        if stored_fingerprint == input_fingerprint or self._stored_analysis_is_current(
            threat
        ):
            return ThreatAIAnalysis(
                ai_summary=threat.ai_summary or "",
                attack_vector=threat.attack_vector or "",
                business_impact=threat.business_impact or "",
                mitre_attack=threat.mitre_attack or [],
                recommendations=threat.recommendations or [],
                confidence_score=threat.confidence_score,
                risk_score=threat.risk_score or 0,
            )

        return None

    def _has_completed_analysis(self, threat: Threat) -> bool:
        return all(
            (
                threat.ai_summary,
                threat.attack_vector,
                threat.business_impact,
                threat.mitre_attack,
                threat.recommendations,
                threat.risk_score is not None,
                threat.last_analyzed,
            )
        )

    def _stored_analysis_is_current(self, threat: Threat) -> bool:
        if threat.last_analyzed is None:
            return False

        last_analyzed = self._as_utc(threat.last_analyzed)
        updated_at = self._as_utc(threat.updated_at)
        return last_analyzed + timedelta(seconds=5) >= updated_at

    def _as_utc(self, value: datetime) -> datetime:
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def _fingerprint(self, prompt: str) -> str:
        return hashlib.sha256(prompt.encode("utf-8")).hexdigest()
