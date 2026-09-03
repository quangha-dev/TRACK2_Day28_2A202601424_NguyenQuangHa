"""The load tool must distinguish rejected HTTP traffic from transport errors."""

from __future__ import annotations

import importlib.util
import io
import json
import urllib.error
from pathlib import Path
from unittest.mock import patch

import pytest

SPEC = importlib.util.spec_from_file_location(
    "load_profile", Path(__file__).resolve().parents[1] / "load-tests" / "run_profile.py"
)
assert SPEC is not None and SPEC.loader is not None
profile = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(profile)


@pytest.mark.parametrize("status", [429, 503])
def test_http_rejection_keeps_its_status(status: int) -> None:
    error = urllib.error.HTTPError("http://localhost/ready", status, "rejected", {}, io.BytesIO())
    with patch.object(profile.urllib.request, "urlopen", side_effect=error):
        _, actual = profile.request("http://localhost")
    assert actual == status


def test_transport_failure_has_no_http_status() -> None:
    with patch.object(profile.urllib.request, "urlopen", side_effect=OSError("unreachable")):
        assert profile.request("http://localhost")[1] == 0


def test_ask_uses_post_and_preserves_unicode_payload() -> None:
    payload = {"asker_id": "demo", "question": "Vai trò của Kafka?"}
    with patch.object(profile.urllib.request, "urlopen", side_effect=OSError("offline")) as send:
        profile.request("http://localhost", endpoint="/api/v1/ask", payload=payload)
    sent = send.call_args.args[0]
    assert sent.get_method() == "POST"
    assert sent.full_url == "http://localhost/api/v1/ask"
    assert json.loads(sent.data) == payload


def test_no_successful_requests_has_no_latency_percentile() -> None:
    assert profile.percentile([], 0.95) is None
