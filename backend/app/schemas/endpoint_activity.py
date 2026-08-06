from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EndpointActivityResponse(BaseModel):
    id: int
    hostname: str
    username: str
    recent_threat_ids: list[int]
    related_incident_ids: list[int]
    detection_timestamps: list[str]
    ai_analysis_status: str
    last_activity_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EndpointActivityListResponse(BaseModel):
    items: list[EndpointActivityResponse]
    total: int
    page: int
    page_size: int
    pages: int
