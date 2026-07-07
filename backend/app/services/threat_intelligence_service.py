import asyncio
import time
from datetime import datetime, timezone
from math import ceil

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai.ai_service import AIService
from app.config.settings import get_settings
from app.models.threat import Threat
from app.models.user import User
from app.repositories.threat_repository import ThreatRepository
from app.schemas.threat_intelligence import (
    ThreatIntelligenceLatestResponse,
    ThreatIntelligenceStatus,
    ThreatIntelligenceSyncResult,
)
from app.threat_intelligence.collectors import CISAKEVCollector, NVDCollector
from app.threat_intelligence.models import NormalizedThreat
from app.utils.logging import get_logger

logger = get_logger(__name__)


def normalize_datetime_for_comparison(value: datetime | None) -> datetime | None:
    if value is None:
        return None

    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def _verify_datetime_normalization() -> None:
    naive_existing = datetime(2026, 1, 1, 10, 0, 0)
    naive_newer = datetime(2026, 1, 1, 11, 0, 0)
    aware_existing = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    aware_newer = datetime(2026, 1, 1, 11, 0, 0, tzinfo=timezone.utc)

    assert normalize_datetime_for_comparison(None) is None
    assert normalize_datetime_for_comparison(naive_existing) == aware_existing
    assert normalize_datetime_for_comparison(aware_existing) == aware_existing
    assert normalize_datetime_for_comparison(aware_newer) > normalize_datetime_for_comparison(
        naive_existing
    )
    assert normalize_datetime_for_comparison(aware_newer) > normalize_datetime_for_comparison(
        aware_existing
    )
    assert normalize_datetime_for_comparison(naive_newer) > normalize_datetime_for_comparison(
        naive_existing
    )


_verify_datetime_normalization()


class ThreatIntelligenceService:
    _last_status = ThreatIntelligenceStatus()

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = ThreatRepository(db)
        self.collectors = [NVDCollector(), CISAKEVCollector()]

    async def sync(self, current_user: User, limit: int | None = None) -> ThreatIntelligenceSyncResult:
        settings = get_settings()
        sync_limit = limit or settings.threat_intel_sync_limit
        started = time.perf_counter()
        result = ThreatIntelligenceSyncResult()
        logger.info("Threat intelligence sync started with limit=%s", sync_limit)
        logger.info("[START] Threat intelligence sync")

        try:
            batches = await asyncio.gather(
                *(collector.fetch(sync_limit) for collector in self.collectors),
            )

            imported_or_updated: list[Threat] = []
            for batch in batches:
                result.fetched += len(batch)
                for normalized in batch:
                    threat, action = self._upsert(normalized, current_user.id)
                    if action == "imported":
                        result.imported += 1
                        imported_or_updated.append(threat)
                    elif action == "updated":
                        result.updated += 1
                        imported_or_updated.append(threat)
                    else:
                        result.skipped_duplicates += 1

            ai_started = time.perf_counter()
            logger.info("[START] AI enrichment")
            result.analyzed = self._enrich_with_ai(imported_or_updated)
            logger.info("[END] AI enrichment (%s ms)", self._elapsed_ms(ai_started))
            result.duration_seconds = round(time.perf_counter() - started, 2)
            self._update_status("SUCCESS", "Threat intelligence sync completed", result)
            logger.info(
                "[END] Threat intelligence sync (%s ms)",
                self._elapsed_ms(started),
            )
            logger.info(
                "Threat intelligence sync completed fetched=%s imported=%s updated=%s "
                "duplicates=%s analyzed=%s failed=%s duration=%s",
                result.fetched,
                result.imported,
                result.updated,
                result.skipped_duplicates,
                result.analyzed,
                result.failed,
                result.duration_seconds,
            )
            return result
        except TimeoutError as exc:
            result.duration_seconds = round(time.perf_counter() - started, 2)
            self._update_status("FAILED", str(exc), result)
            logger.exception(
                "[TIMEOUT] Threat intelligence sync after %s ms",
                self._elapsed_ms(started),
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Threat intelligence sync failed.",
            ) from exc
        except Exception as exc:
            result.duration_seconds = round(time.perf_counter() - started, 2)
            self._update_status("FAILED", str(exc), result)
            logger.exception(
                "[ERROR] Threat intelligence sync failed after %s ms",
                self._elapsed_ms(started),
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Threat intelligence sync failed.",
            ) from exc

    def latest(self, page: int, page_size: int) -> ThreatIntelligenceLatestResponse:
        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page must be greater than or equal to 1",
            )
        if page_size < 1 or page_size > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page size must be between 1 and 100",
            )

        statement = (
            select(Threat)
            .where(Threat.source_feed.is_not(None))
            .order_by(Threat.modified_date.desc().nullslast(), Threat.id.desc())
        )
        total = self.db.scalar(select(func.count()).select_from(statement.subquery())) or 0
        items = self.db.scalars(
            statement.offset((page - 1) * page_size).limit(page_size)
        ).all()
        return ThreatIntelligenceLatestResponse(
            items=list(items),
            total=total,
            page=page,
            page_size=page_size,
            pages=ceil(total / page_size) if total else 0,
        )

    def status(self) -> ThreatIntelligenceStatus:
        imported_total = (
            self.db.scalar(
                select(func.count()).select_from(
                    select(Threat.id).where(Threat.source_feed.is_not(None)).subquery()
                )
            )
            or 0
        )
        self.__class__._last_status.imported_total = imported_total
        return self.__class__._last_status

    def _upsert(self, normalized: NormalizedThreat, created_by: int) -> tuple[Threat, str]:
        duplicate_started = time.perf_counter()
        logger.info("[START] Duplicate detection %s", normalized.cve_id)
        existing = self.repository.get_threat_by_cve_id(normalized.cve_id)
        logger.info(
            "[END] Duplicate detection %s (%s ms)",
            normalized.cve_id,
            self._elapsed_ms(duplicate_started),
        )
        payload = normalized.to_threat_payload()

        if existing is None:
            save_started = time.perf_counter()
            logger.info("[START] Database save %s", normalized.cve_id)
            threat = self.repository.create_imported_threat(payload, created_by)
            logger.info(
                "[END] Database save %s (%s ms)",
                normalized.cve_id,
                self._elapsed_ms(save_started),
            )
            return threat, "imported"

        if self._is_newer(normalized.modified_date, existing.modified_date):
            save_started = time.perf_counter()
            logger.info("[START] Database save %s", normalized.cve_id)
            threat = self.repository.update_imported_threat(existing, payload)
            logger.info(
                "[END] Database save %s (%s ms)",
                normalized.cve_id,
                self._elapsed_ms(save_started),
            )
            return threat, "updated"

        return existing, "duplicate"

    def _is_newer(
        self,
        incoming_modified: datetime | None,
        existing_modified: datetime | None,
    ) -> bool:
        normalized_incoming = normalize_datetime_for_comparison(incoming_modified)
        normalized_existing = normalize_datetime_for_comparison(existing_modified)

        if normalized_incoming is None:
            return False
        if normalized_existing is None:
            return True
        return normalized_incoming > normalized_existing

    def _enrich_with_ai(self, threats: list[Threat]) -> int:
        analyzed = 0
        ai_service = AIService()

        for threat in threats:
            cve_id = threat.cve_id or str(threat.id)
            logger.info("Current CVE ID: %s", cve_id)
            logger.info("Current Gemini model: %s", ai_service.provider.model_manager.get_model())
            analysis = ai_service.analyze_threat(threat)
            ai_service.apply_analysis(threat, analysis)
            self.repository.save_analysis(threat)
            logger.info("Save completed for AI enrichment %s", cve_id)
            analyzed += 1
            logger.info("AI enrichment completed for %s", cve_id)

        return analyzed

    def _elapsed_ms(self, started: float) -> int:
        return int((time.perf_counter() - started) * 1000)

    def _update_status(
        self,
        sync_status: str,
        message: str,
        result: ThreatIntelligenceSyncResult,
    ) -> None:
        self.__class__._last_status = ThreatIntelligenceStatus(
            last_sync_at=datetime.now(timezone.utc),
            last_status=sync_status,
            last_message=message,
            imported_total=result.imported + result.updated + result.skipped_duplicates,
        )
