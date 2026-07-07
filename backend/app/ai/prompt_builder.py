from app.models.threat import Threat


class ThreatPromptBuilder:
    def build(self, threat: Threat) -> str:
        return (
            "You are SentinelAI, a cybersecurity threat intelligence analyst. "
            "Analyze the threat below and respond with JSON only. Do not include "
            "Markdown, code fences, comments, or prose outside the JSON object.\n\n"
            "Required JSON schema:\n"
            "{\n"
            '  "ai_summary": "string, 2-4 concise sentences",\n'
            '  "attack_vector": "string",\n'
            '  "business_impact": "string",\n'
            '  "mitre_attack": ["string"],\n'
            '  "recommendations": ["string"],\n'
            '  "confidence_score": number between 0 and 100,\n'
            '  "risk_score": number between 0 and 100\n'
            "}\n\n"
            "Threat details:\n"
            f"Title: {threat.title}\n"
            f"Description: {threat.description}\n"
            f"Category: {threat.category.value}\n"
            f"Severity: {threat.severity.value}\n"
            f"Status: {threat.status.value}\n"
            f"Source: {threat.source}\n"
            f"Existing confidence score: {threat.confidence_score}\n"
            f"Detected at: {threat.detected_at.isoformat()}\n"
        )
