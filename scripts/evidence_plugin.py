"""Optional pytest recorder: preserves real journey results without changing tests.

Use ``python -m pytest integration-tests -p scripts.evidence_plugin``. This records fixture
values and test outcomes; it never turns an error or skipped test into a pass.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

RESULTS: list[dict[str, Any]] = []
OUT = Path("evidence")


def write(name: str, payload: dict[str, Any]) -> None:
    OUT.mkdir(exist_ok=True)
    (OUT / name).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[Any]) -> Any:
    result = yield
    report = result.get_result()
    if report.when == "call" or (report.when == "setup" and not report.passed):
        RESULTS.append({
            "test": report.nodeid, "phase": report.when,
            "outcome": report.outcome, "duration_seconds": report.duration,
        })
    if report.when != "call" or not report.passed:
        return
    if item.name == "test_the_journey_is_queryable_by_its_trace_id":
        from lab28_platform import delta_store
        from lab28_platform.model_registry import ReleaseRegistry
        from lab28_platform.settings import Settings

        journey = item.funcargs["journey"]
        settings = Settings.from_env()
        write("j1-happy-path.json", {
            "captured_at_utc": datetime.now(UTC).isoformat(),
            "scope": "ingestion and materialization; GPU answer UNVERIFIED",
            "trace_id": journey.trace_id,
            "dag_run_id": journey.dag_run["dag_run_id"],
            "delta_version": delta_store.current_version(settings.feedback_table),
            "mlflow_release": ReleaseRegistry(settings.mlflow).resolve().to_dict(),
            "asker_id": journey.asker_id, "doc_id": journey.doc_id,
            "idempotency_key": journey.idempotency_key,
            "span_names": sorted(item.funcargs["traces"].span_names(journey.trace_id)),
            "assertion_passed": report.nodeid,
        })
    if item.name == "test_the_vector_store_holds_exactly_one_point_for_the_document":
        from lab28_platform import delta_store

        replay = item.funcargs["replay"]
        settings = item.funcargs["settings"]
        rows = [
            row for row in delta_store.read_rows(settings.feedback_table)
            if row.get("asker_id") == replay.asker_id
        ]
        write("j2-replay.json", {
            "captured_at_utc": datetime.now(UTC).isoformat(),
            "asker_id": replay.asker_id, "doc_id": replay.doc_id,
            "idempotency_key": replay.idempotency_key,
            "accepted": replay.accepted,
            "first_run": replay.first_run, "second_run": replay.second_run,
            "version_after_first": replay.version_after_first,
            "version_after_second": delta_store.current_version(settings.feedback_table),
            "rows_after_first": replay.rows_after_first, "rows_after_second": rows,
            "assertion_passed": report.nodeid,
        })
    if "rolled_back" in item.funcargs and "promoted" in item.funcargs:
        promoted = item.funcargs["promoted"]
        write("j3-rollback.json", {
            "captured_at_utc": datetime.now(UTC).isoformat(),
            "previous_version": promoted.previous_version,
            "promoted_release": promoted.release.to_dict(),
            "rolled_back_release": item.funcargs["rolled_back"].to_dict(),
            "assertion_passed": report.nodeid,
        })
    if item.name == "test_the_good_record_in_the_same_batch_still_reached_the_lakehouse":
        from lab28_platform import delta_store

        batch = item.funcargs["poison_batch"]
        settings = item.funcargs["settings"]
        write("j4-poison-batch.json", {
            "captured_at_utc": datetime.now(UTC).isoformat(),
            "asker_id": batch.asker_id, "poison_key": batch.key,
            "dag_run": batch.run,
            "dlq_before": batch.dead_letters_before,
            "dlq_after": batch.dead_letters_after,
            "dead_letters": batch.envelopes,
            "good_rows": [row for row in delta_store.read_rows(settings.feedback_table)
                          if row.get("asker_id") == batch.asker_id],
            "assertion_passed": report.nodeid,
        })
    if item.name == "test_the_replayed_event_does_not_duplicate_the_row":
        from lab28_platform import delta_store

        replayed = item.funcargs["replayed"]
        settings = item.funcargs["settings"]
        write("j4-dlq-replay.json", {
            "captured_at_utc": datetime.now(UTC).isoformat(),
            "asker_id": replayed.asker_id, "idempotency_key": replayed.idempotency_key,
            "replay_result": replayed.result, "dag_run": replayed.run,
            "rows": [row for row in delta_store.read_rows(settings.feedback_table)
                     if row.get("asker_id") == replayed.asker_id],
            "assertion_passed": report.nodeid,
        })
    if item.name == "test_the_platform_ends_where_it_started":
        baseline = item.funcargs["baseline"]
        response = item.funcargs["api"].get("/ready")
        write("j4-dependency-recovery.json", {
            "captured_at_utc": datetime.now(UTC).isoformat(),
            "baseline": {"status_code": baseline.status_code, "status": baseline.status},
            "after_recovery": {"status_code": response.status_code, "body": response.json()},
            "tests": [result for result in RESULTS if "test_j4_" in result["test"]],
        })


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    write("journey-results.json", {
        "finished_at_utc": datetime.now(UTC).isoformat(),
        "exit_code": exitstatus, "tests": RESULTS,
    })
