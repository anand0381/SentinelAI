import json

from pydantic import BaseModel, Field, ValidationError, field_validator


class ThreatAIAnalysis(BaseModel):
    ai_summary: str = Field(..., min_length=20, max_length=2000)
    attack_vector: str = Field(..., min_length=2, max_length=300)
    business_impact: str = Field(..., min_length=10, max_length=2000)
    mitre_attack: list[str] = Field(..., min_length=1, max_length=10)
    recommendations: list[str] = Field(..., min_length=1, max_length=10)
    confidence_score: float = Field(..., ge=0, le=100)
    risk_score: float = Field(..., ge=0, le=100)

    @field_validator("ai_summary", "attack_vector", "business_impact")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("mitre_attack", "recommendations")
    @classmethod
    def strip_list_items(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values if value and value.strip()]
        if not cleaned:
            raise ValueError("At least one non-empty item is required")
        return cleaned


class AIResponseParser:
    def parse(self, raw_response: str) -> ThreatAIAnalysis:
        payload = self._extract_json(raw_response)
        try:
            return ThreatAIAnalysis.model_validate(payload)
        except ValidationError as exc:
            raise ValueError("AI response did not match the required analysis schema") from exc

    def _extract_json(self, raw_response: str) -> dict[str, object]:
        text = raw_response.strip()
        if not text:
            raise ValueError("AI provider returned an empty response")

        if text.startswith("```"):
            text = text.strip("`").strip()
            if text.lower().startswith("json"):
                text = text[4:].strip()

        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end < start:
            raise ValueError("AI provider response did not contain a JSON object")

        try:
            parsed = json.loads(text[start : end + 1])
        except json.JSONDecodeError as exc:
            raise ValueError("AI provider response was not valid JSON") from exc

        if not isinstance(parsed, dict):
            raise ValueError("AI provider response must be a JSON object")

        return parsed
