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
