"""Command-line entry point for the SentinelAI endpoint monitoring agent."""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path


if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parent.parent))

from endpoint_agent.collectors import collect_endpoint_telemetry
from endpoint_agent.config import AgentConfig, load_config
from endpoint_agent.sender import TelemetrySender


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="SentinelAI standalone endpoint monitoring agent"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Collect and print telemetry once, then exit.",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=None,
        help="Collect telemetry a fixed number of times, then exit.",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=None,
        help="Override polling interval in seconds for this run.",
    )
    return parser


def _with_interval_override(config: AgentConfig, interval: int | None) -> AgentConfig:
    if interval is None or interval <= 0:
        return config

    return AgentConfig(
        backend_url=config.backend_url,
        agent_id=config.agent_id,
        polling_interval_seconds=interval,
    )


def run_agent(config: AgentConfig, once: bool, iterations: int | None) -> None:
    logger = logging.getLogger(__name__)
    sender = TelemetrySender(config.backend_url)
    completed_iterations = 0

    logger.info(
        "Starting endpoint agent id=%s interval=%ss backend_url=%s",
        config.agent_id,
        config.polling_interval_seconds,
        config.backend_url,
    )

    while True:
        try:
            telemetry = collect_endpoint_telemetry(config)
            sender.emit(telemetry.to_dict())
        except Exception:
            logger.exception("Endpoint telemetry collection cycle failed")

        completed_iterations += 1
        if once or (iterations is not None and completed_iterations >= iterations):
            logger.info("Endpoint agent completed requested collection run")
            return

        time.sleep(config.polling_interval_seconds)


def main() -> None:
    configure_logging()
    args = build_parser().parse_args()
    config = _with_interval_override(load_config(), args.interval)
    iterations = 1 if args.once else args.iterations
    run_agent(config=config, once=args.once, iterations=iterations)


if __name__ == "__main__":
    main()
