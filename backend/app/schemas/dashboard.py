from pydantic import BaseModel


class ChartDataset(BaseModel):
    label: str
    data: list[int]


class ChartData(BaseModel):
    labels: list[str]
    datasets: list[ChartDataset]


class DashboardSummary(BaseModel):
    total_threats: int
    total_incidents: int
    critical_threats: int
    open_incidents: int
    high_priority_incidents: int
    active_incidents: int = 0
    correlated_incidents: int = 0
    average_threats_per_incident: float = 0
    most_affected_endpoint: str | None = None
