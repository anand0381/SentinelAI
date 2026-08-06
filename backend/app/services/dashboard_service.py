from app.repositories.dashboard_repository import DashboardRepository


class DashboardService:
    def __init__(self, dashboard_repository: DashboardRepository) -> None:
        self.dashboard_repository = dashboard_repository

    def get_summary(self) -> dict[str, int]:
        return {
            "total_threats": self.dashboard_repository.count_threats(),
            "total_incidents": self.dashboard_repository.count_incidents(),
            "critical_threats": self.dashboard_repository.count_critical_threats(),
            "open_incidents": self.dashboard_repository.count_open_incidents(),
            "high_priority_incidents": (
                self.dashboard_repository.count_high_priority_incidents()
            ),
            "active_incidents": self.dashboard_repository.count_active_incidents(),
            "correlated_incidents": (
                self.dashboard_repository.count_correlated_incidents()
            ),
            "average_threats_per_incident": (
                self.dashboard_repository.average_threats_per_incident()
            ),
            "most_affected_endpoint": self.dashboard_repository.most_affected_endpoint(),
        }

    def get_threat_severity(self) -> dict[str, list[object]]:
        return self._single_dataset_chart(
            label="Threats by Severity",
            rows=self.dashboard_repository.threat_counts_by_severity(),
        )

    def get_threat_category(self) -> dict[str, list[object]]:
        return self._single_dataset_chart(
            label="Threats by Category",
            rows=self.dashboard_repository.threat_counts_by_category(),
        )

    def get_incident_status(self) -> dict[str, list[object]]:
        return self._single_dataset_chart(
            label="Incidents by Status",
            rows=self.dashboard_repository.incident_counts_by_status(),
        )

    def get_monthly_trends(self) -> dict[str, list[object]]:
        threat_counts = {
            month: count
            for month, count in self.dashboard_repository.monthly_threat_counts()
            if month
        }
        incident_counts = {
            month: count
            for month, count in self.dashboard_repository.monthly_incident_counts()
            if month
        }
        labels = sorted(set(threat_counts) | set(incident_counts))

        return {
            "labels": labels,
            "datasets": [
                {
                    "label": "Threats",
                    "data": [threat_counts.get(label, 0) for label in labels],
                },
                {
                    "label": "Incidents",
                    "data": [incident_counts.get(label, 0) for label in labels],
                },
            ],
        }

    def _single_dataset_chart(
        self,
        label: str,
        rows: list[tuple[object, int]],
    ) -> dict[str, list[object]]:
        labels = [self._label_value(row_label) for row_label, _ in rows]
        data = [count for _, count in rows]
        return {
            "labels": labels,
            "datasets": [
                {
                    "label": label,
                    "data": data,
                }
            ],
        }

    def _label_value(self, value: object) -> str:
        return getattr(value, "value", str(value))
