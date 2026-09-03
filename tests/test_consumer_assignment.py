"""Regression checks for an empty batch reported before Kafka group assignment."""

from unittest.mock import Mock

import pytest

from lab28_platform import event_bus
from lab28_platform.contracts import FeedbackPayload, IngestionEvent


def message() -> Mock:
    event = IngestionEvent(
        idempotency_key="assignment-test", entity_id="asker-1",
        payload=FeedbackPayload(asker_id="asker-1", text="Test event", rating=5),
    )
    result = Mock()
    result.error.return_value = None
    result.headers.return_value = []
    result.value.return_value = event.model_dump_json().encode()
    result.key.return_value = b"asker-1"
    result.topic.return_value = "data.raw"
    result.partition.return_value = 0
    result.offset.return_value = 0
    return result


def consumer(polls: list) -> event_bus.BatchConsumer:
    result = object.__new__(event_bus.BatchConsumer)
    result._consumer = Mock()
    result._consumer.poll.side_effect = polls
    result._consumer.assignment.return_value = [object()]
    return result


def test_group_join_does_not_count_as_an_empty_topic() -> None:
    client = consumer([None] * 4 + [message()] + [None] * 3)
    client._consumer.assignment.side_effect = [[]] * 4 + [[object()]] * 3
    decoded, poison = client.poll_batch(10)
    assert len(decoded) == 1
    assert poison == []


def test_idle_polls_must_be_consecutive() -> None:
    client = consumer([None, None, message(), None, None, message(), None, None, None])
    decoded, _ = client.poll_batch(10)
    assert len(decoded) == 2


def test_missing_assignment_is_an_error_not_success(monkeypatch: pytest.MonkeyPatch) -> None:
    client = consumer([None])
    client._consumer.assignment.return_value = []
    moments = iter([0.0, 31.0])
    monkeypatch.setattr(event_bus.time, "monotonic", lambda: next(moments))
    with pytest.raises(event_bus.BrokerUnavailable, match="assignment timed out"):
        client.poll_batch(10)
