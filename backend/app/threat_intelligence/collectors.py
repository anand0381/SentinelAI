import asyncio
import json
import time
from datetime import datetime, timedelta, timezone
from urllib import error, parse, request

from app.config.settings import get_settings
from app.models.threat import ThreatSeverity
from app.threat_intelligence.models import NormalizedThreat
from app.utils.logging import get_logger

logger = get_logger(__name__)


class ThreatFeedCollector:
    feed_name: str

    async def fetch(self, limit: int) -> list[NormalizedThreat]:
        raise NotImplementedError

    async def _fetch_json(self, url: str, timeout: int) -> dict[str, object]:
        last_error: Exception | None = None
        stage_started = time.perf_counter()
        logger.info("[START] Downloading %s", self.feed_name)

        for attempt in range(1, 4):
            try:
                logger.info("Downloading threat feed %s attempt %s", self.feed_name, attempt)
                payload = await asyncio.to_thread(self._read_json, url, timeout)
                logger.info(
                    "[END] Downloading %s (%s ms)",
                    self.feed_name,
                    self._elapsed_ms(stage_started),
                )
                return payload
            except TimeoutError as exc:
                last_error = exc
                logger.exception(
                    "[TIMEOUT] Downloading %s attempt %s after %s ms",
                    self.feed_name,
                    attempt,
                    self._elapsed_ms(stage_started),
                )
                await asyncio.sleep(attempt)
            except (error.URLError, json.JSONDecodeError) as exc:
                last_error = exc
                logger.exception(
                    "Threat feed %s download failed on attempt %s: %s",
                    self.feed_name,
                    attempt,
                    exc,
                )
                await asyncio.sleep(attempt)

        logger.error(
            "[ERROR] Downloading %s failed after %s ms",
            self.feed_name,
            self._elapsed_ms(stage_started),
            exc_info=(type(last_error), last_error, last_error.__traceback__)
            if last_error
            else None,
        )
        raise RuntimeError(f"{self.feed_name} feed download failed") from last_error

    def _read_json(self, url: str, timeout: int) -> dict[str, object]:
        feed_request = request.Request(url=url, headers={"User-Agent": "SentinelAI/1.0"})
        with request.urlopen(feed_request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def _elapsed_ms(self, started: float) -> int:
        return int((time.perf_counter() - started) * 1000)


class NVDCollector(ThreatFeedCollector):
    feed_name = "NVD"

    async def fetch(self, limit: int) -> list[NormalizedThreat]:
        settings = get_settings()
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=14)
        query = parse.urlencode(
            {
                "pubStartDate": start.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "pubEndDate": now.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "resultsPerPage": limit,
                "startIndex": 0,
            }
        )
        payload = await self._fetch_json(
            f"{settings.nvd_api_url}?{query}",
            settings.threat_intel_timeout_seconds,
        )
        vulnerabilities = payload.get("vulnerabilities")
        if not isinstance(vulnerabilities, list):
            raise ValueError("NVD feed response did not contain vulnerabilities")

        parse_started = time.perf_counter()
        logger.info("[START] Parsing feeds (NVD)")
        try:
            normalized = [
                self._normalize(item)
                for item in vulnerabilities[:limit]
                if isinstance(item, dict)
            ]
            logger.info("[END] Parsing feeds (NVD) (%s ms)", self._elapsed_ms(parse_started))
            return normalized
        except Exception:
            logger.exception("[ERROR] Parsing feeds (NVD)")
            raise

    def _normalize(self, item: dict[str, object]) -> NormalizedThreat:
        cve = item.get("cve", {})
        if not isinstance(cve, dict):
            raise ValueError("NVD vulnerability missing CVE object")

        cve_id = str(cve.get("id", "")).strip()
        description = self._description(cve)
        score, severity = self._score_and_severity(cve)
        published = self._parse_datetime(cve.get("published"))
        modified = self._parse_datetime(cve.get("lastModified"))
        reference_url = self._reference_url(cve)
        vendor_product = self._vendor_product(cve)

        return NormalizedThreat(
            cve_id=cve_id,
            title=f"{cve_id} - {description[:130]}",
            description=description,
            severity=severity,
            source="NVD CVE API",
            source_feed="NVD",
            detected_at=modified or published or datetime.now(timezone.utc),
            published_date=published,
            modified_date=modified,
            cvss_score=score,
            vendor_product=vendor_product,
            reference_url=reference_url,
            tags=["cve", "nvd"],
            confidence_score=85,
        )

    def _description(self, cve: dict[str, object]) -> str:
        descriptions = cve.get("descriptions", [])
        if isinstance(descriptions, list):
            for item in descriptions:
                if isinstance(item, dict) and item.get("lang") == "en":
                    return str(item.get("value", "")).strip()
        return "No CVE description was provided by NVD."

    def _score_and_severity(self, cve: dict[str, object]) -> tuple[float | None, ThreatSeverity]:
        metrics = cve.get("metrics", {})
        if not isinstance(metrics, dict):
            return None, ThreatSeverity.MEDIUM

        metric_keys = ("cvssMetricV40", "cvssMetricV31", "cvssMetricV30", "cvssMetricV2")
        for key in metric_keys:
            values = metrics.get(key)
            if isinstance(values, list) and values:
                cvss_data = values[0].get("cvssData", {}) if isinstance(values[0], dict) else {}
                score = cvss_data.get("baseScore") if isinstance(cvss_data, dict) else None
                severity = values[0].get("baseSeverity") or cvss_data.get("baseSeverity")
                return self._float_or_none(score), self._severity(str(severity or "MEDIUM"))

        return None, ThreatSeverity.MEDIUM

    def _reference_url(self, cve: dict[str, object]) -> str | None:
        references = cve.get("references", {})
        data = references.get("referenceData", []) if isinstance(references, dict) else []
        if isinstance(data, list) and data:
            first = data[0]
            if isinstance(first, dict):
                return str(first.get("url") or "") or None
        return None

    def _vendor_product(self, cve: dict[str, object]) -> str | None:
        configurations = cve.get("configurations", [])
        if not isinstance(configurations, list):
            return None

        for config in configurations:
            nodes = config.get("nodes", []) if isinstance(config, dict) else []
            for node in nodes if isinstance(nodes, list) else []:
                matches = node.get("cpeMatch", []) if isinstance(node, dict) else []
                for match in matches if isinstance(matches, list) else []:
                    criteria = match.get("criteria", "") if isinstance(match, dict) else ""
                    parts = str(criteria).split(":")
                    if len(parts) > 5:
                        return f"{parts[3]} / {parts[4]}".replace("_", " ")
        return None

    def _parse_datetime(self, value: object) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None

    def _severity(self, value: str) -> ThreatSeverity:
        normalized = value.upper()
        if normalized in ThreatSeverity.__members__:
            return ThreatSeverity[normalized]
        return ThreatSeverity.MEDIUM

    def _float_or_none(self, value: object) -> float | None:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None


class CISAKEVCollector(ThreatFeedCollector):
    feed_name = "CISA"

    async def fetch(self, limit: int) -> list[NormalizedThreat]:
        settings = get_settings()
        payload = await self._fetch_json(settings.cisa_kev_url, settings.threat_intel_timeout_seconds)
        vulnerabilities = payload.get("vulnerabilities")
        if not isinstance(vulnerabilities, list):
            raise ValueError("CISA KEV response did not contain vulnerabilities")

        parse_started = time.perf_counter()
        logger.info("[START] Parsing feeds (CISA)")
        try:
            normalized = [
                self._normalize(item)
                for item in vulnerabilities[:limit]
                if isinstance(item, dict) and item.get("cveID")
            ]
            logger.info("[END] Parsing feeds (CISA) (%s ms)", self._elapsed_ms(parse_started))
            return normalized
        except Exception:
            logger.exception("[ERROR] Parsing feeds (CISA)")
            raise

    def _normalize(self, item: dict[str, object]) -> NormalizedThreat:
        cve_id = str(item.get("cveID", "")).strip()
        vendor = str(item.get("vendorProject") or "").strip()
        product = str(item.get("product") or "").strip()
        description = str(item.get("shortDescription") or item.get("vulnerabilityName") or "").strip()
        date_added = self._parse_date(item.get("dateAdded"))
        tags = ["cve", "cisa-kev", "known-exploited"]

        ransomware = str(item.get("knownRansomwareCampaignUse") or "").lower()
        if ransomware == "known":
            tags.append("ransomware")

        return NormalizedThreat(
            cve_id=cve_id,
            title=f"{cve_id} - {item.get('vulnerabilityName') or product or 'Known exploited vulnerability'}",
            description=description or "CISA KEV catalog entry without a description.",
            severity=ThreatSeverity.HIGH,
            source="CISA KEV Catalog",
            source_feed="CISA",
            detected_at=date_added or datetime.now(timezone.utc),
            published_date=date_added,
            modified_date=date_added,
            vendor_product=" / ".join(value for value in (vendor, product) if value) or None,
            reference_url="https://www.cisa.gov/known-exploited-vulnerabilities-catalog",
            tags=tags,
            confidence_score=90,
        )

    def _parse_date(self, value: object) -> datetime | None:
        if not value:
            return None
        for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
            try:
                parsed = datetime.strptime(str(value), fmt)
                return parsed.replace(tzinfo=timezone.utc)
            except ValueError:
                continue
        return None
