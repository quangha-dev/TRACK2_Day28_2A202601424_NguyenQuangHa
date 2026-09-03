"""Measure the real readiness or RAG endpoint without hiding HTTP errors."""

from __future__ import annotations

import argparse
import json
import math
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path


def percentile(values: list[float], quantile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, math.ceil(quantile * len(ordered)) - 1)]


def request(
    url: str,
    *,
    endpoint: str = "/ready",
    payload: dict[str, object] | None = None,
    timeout: float = 10.0,
) -> tuple[float, int]:
    started = time.perf_counter()
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        f"{url.rstrip('/')}{endpoint}",
        data=body,
        headers={"Content-Type": "application/json"} if body is not None else {},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            response.read()
            status = response.status
    except urllib.error.HTTPError as error:
        status = error.code
        error.close()
    except (OSError, urllib.error.URLError):
        status = 0
    return (time.perf_counter() - started) * 1000, status


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8080")
    parser.add_argument("--endpoint", choices=["/ready", "/api/v1/ask"], default="/ready")
    parser.add_argument("--requests", type=int, default=100)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--warmup", type=int, default=0)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--asker-id", default="demo")
    parser.add_argument("--question", default="Vai trò của Delta Lake trong nền tảng là gì?")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.requests < 1 or args.workers < 1 or args.warmup < 0 or args.timeout <= 0:
        parser.error("requests, workers and timeout must be positive; warmup must be non-negative")
    payload = (
        {"asker_id": args.asker_id, "question": args.question, "top_k": 3}
        if args.endpoint == "/api/v1/ask"
        else None
    )

    def call(_: int) -> tuple[float, int]:
        return request(args.url, endpoint=args.endpoint, payload=payload, timeout=args.timeout)

    for number in range(args.warmup):
        call(number)
    started_at = datetime.now(UTC).isoformat()
    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(call, range(args.requests)))
    elapsed = time.perf_counter() - started
    durations = [duration for duration, _ in results]
    successes = [duration for duration, status in results if 200 <= status < 300]
    statuses: dict[str, int] = {}
    for _, status in results:
        statuses[str(status)] = statuses.get(str(status), 0) + 1
    def quantiles(values: list[float]) -> dict[str, float | None]:
        return {
            name: percentile(values, quantile)
            for name, quantile in (("p50", 0.5), ("p95", 0.95), ("p99", 0.99))
        }

    report = {
        "started_at_utc": started_at,
        "endpoint": args.endpoint,
        "method": "POST" if payload is not None else "GET",
        "requests": args.requests,
        "workers": args.workers,
        "warmup_requests": args.warmup,
        "duration_seconds": elapsed,
        "throughput_rps": args.requests / elapsed,
        "successful_rps": len(successes) / elapsed,
        "status_counts": statuses,
        "error_rate": (args.requests - len(successes)) / args.requests,
        "latency_ms": quantiles(durations),
        "successful_latency_ms": quantiles(successes),
        "note": "Status 0 means transport failure; all-request latency includes errors.",
    }
    output = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    print(output, end="")
    if not successes:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
