"""Tests for AgentExecutionManager execution lifecycle."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from models.execution import Execution, ExecutionStatus
from services.execution_manager import AgentExecutionManager, ExecutionContext
from services.retry_policy import FallbackPolicy, RetryPolicy


def make_manager(db_session, monkeypatch=None):
    manager = AgentExecutionManager(db_session)
    return manager


def test_create_execution(db_session):
    manager = make_manager(db_session)
    execution = manager.create_execution(
        agent_id=1,
        conversation_id=10,
        input_messages=[{"role": "user", "content": "hi"}],
    )
    assert execution.execution_id is not None
    assert execution.status == ExecutionStatus.IDLE
    assert execution.agent_id == 1
    assert execution.conversation_id == 10


def test_submit_transitions_to_queued(db_session):
    manager = make_manager(db_session)
    execution = manager.create_execution(agent_id=1)
    updated = manager.submit(execution.execution_id)
    assert updated.status == ExecutionStatus.QUEUED


def test_submit_invalid_state_raises(db_session):
    manager = make_manager(db_session)
    execution = manager.create_execution(agent_id=1)
    manager.submit(execution.execution_id)
    with pytest.raises(ValueError):
        manager.submit(execution.execution_id)


def test_cancel_queued_execution(db_session):
    manager = make_manager(db_session)
    execution = manager.create_execution(agent_id=1)
    manager.submit(execution.execution_id)
    cancelled = manager.cancel(execution.execution_id)
    assert cancelled.status == ExecutionStatus.CANCELLED


def test_cancel_terminal_state_raises(db_session):
    manager = make_manager(db_session)
    execution = manager.create_execution(agent_id=1)
    manager.submit(execution.execution_id)
    manager._transition_status(execution, ExecutionStatus.COMPLETED)
    with pytest.raises(ValueError):
        manager.cancel(execution.execution_id)


def test_get_execution(db_session):
    manager = make_manager(db_session)
    execution = manager.create_execution(agent_id=1)
    fetched = manager.get_execution(execution.execution_id)
    assert fetched.execution_id == execution.execution_id


def test_get_execution_not_found_raises(db_session):
    manager = make_manager(db_session)
    with pytest.raises(ValueError):
        manager._get_execution("missing-id")


def test_list_active_executions(db_session):
    manager = make_manager(db_session)
    e1 = manager.create_execution(agent_id=1)
    manager.submit(e1.execution_id)
    e2 = manager.create_execution(agent_id=1)
    manager.submit(e2.execution_id)
    manager._transition_status(e2, ExecutionStatus.COMPLETED)
    active = manager.list_active_executions()
    assert len(active) == 1
    assert active[0].execution_id == e1.execution_id


def test_get_execution_history(db_session):
    manager = make_manager(db_session)
    e1 = manager.create_execution(agent_id=1)
    manager.submit(e1.execution_id)
    manager._transition_status(e1, ExecutionStatus.COMPLETED)
    history = manager.get_execution_history(agent_id=1)
    assert len(history) == 1
    assert history[0].execution_id == e1.execution_id


@pytest.mark.asyncio
async def test_execute_non_streaming_success(db_session, monkeypatch):
    manager = make_manager(db_session)
    execution = manager.create_execution(
        agent_id=1, input_messages=[{"role": "user", "content": "hi"}]
    )
    manager.submit(execution.execution_id)

    fake_agent = MagicMock()
    fake_agent.agent_model = MagicMock()
    fake_config = {"provider_id": 1, "model": "m1"}

    async def fake_chat(*, messages, provider_id, model, **kwargs):
        assert provider_id == 1
        assert model == "m1"
        return "hello"

    with patch.object(
        manager.agent_manager, "resolve_agent", return_value=fake_agent
    ), patch.object(
        manager.agent_manager, "get_agent_config", return_value=fake_config
    ), patch.object(
        manager.agent_manager, "validate_execution"
    ), patch.object(
        manager.ai_runtime, "chat", side_effect=fake_chat
    ):
        completed = await manager.execute(execution.execution_id)

    assert completed.status == ExecutionStatus.COMPLETED
    assert completed.output_response == "hello"
    assert completed.latency_ms is not None


@pytest.mark.asyncio
async def test_execute_stream_success(db_session, monkeypatch):
    manager = make_manager(db_session)
    execution = manager.create_execution(
        agent_id=1, input_messages=[{"role": "user", "content": "hi"}]
    )
    manager.submit(execution.execution_id)

    fake_agent = MagicMock()
    fake_agent.agent_model = MagicMock()
    fake_config = {"provider_id": 1, "model": "m1"}

    async def fake_stream(*, messages, provider_id, model, **kwargs):
        for chunk in ["hel", "lo"]:
            yield chunk

    with patch.object(
        manager.agent_manager, "resolve_agent", return_value=fake_agent
    ), patch.object(
        manager.agent_manager, "get_agent_config", return_value=fake_config
    ), patch.object(
        manager.agent_manager, "validate_execution"
    ), patch.object(
        manager.ai_runtime, "stream", side_effect=fake_stream
    ):
        chunks = []
        async for chunk in manager.execute_stream(execution.execution_id):
            chunks.append(chunk)

    assert chunks == ["hel", "lo"]
    assert execution.output_response == "hello"
    assert execution.streaming_chunks == 2
    assert execution.status == ExecutionStatus.COMPLETED


@pytest.mark.asyncio
async def test_execute_stream_cancelled(db_session, monkeypatch):
    manager = make_manager(db_session)
    execution = manager.create_execution(
        agent_id=1, input_messages=[{"role": "user", "content": "hi"}]
    )
    manager.submit(execution.execution_id)

    fake_agent = MagicMock()
    fake_agent.agent_model = MagicMock()
    fake_config = {"provider_id": 1, "model": "m1"}

    # Import the module-level _active_executions
    from services.execution_manager import _active_executions

    async def fake_stream(*, messages, provider_id, model, **kwargs):
        yield "start"
        ctx = _active_executions.get(execution.execution_id)
        if ctx:
            ctx.cancel_event.set()
        yield "end"

    with patch.object(
        manager.agent_manager, "resolve_agent", return_value=fake_agent
    ), patch.object(
        manager.agent_manager, "get_agent_config", return_value=fake_config
    ), patch.object(
        manager.agent_manager, "validate_execution"
    ), patch.object(
        manager.ai_runtime, "stream", side_effect=fake_stream
    ):
        chunks = []
        async for chunk in manager.execute_stream(execution.execution_id):
            chunks.append(chunk)

    assert "start" in chunks
    assert execution.status == ExecutionStatus.CANCELLED


@pytest.mark.asyncio
async def test_execute_with_retry_then_success(db_session, monkeypatch):
    manager = make_manager(db_session)
    execution = manager.create_execution(
        agent_id=1, input_messages=[{"role": "user", "content": "hi"}]
    )
    manager.submit(execution.execution_id)

    fake_agent = MagicMock()
    fake_agent.agent_model = MagicMock()
    fake_config = {"provider_id": 1, "model": "m1"}

    call_count = 0

    async def flaky_chat(*, messages, provider_id, model, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise RuntimeError("rate limit exceeded")
        return "ok"

    with patch.object(
        manager.agent_manager, "resolve_agent", return_value=fake_agent
    ), patch.object(
        manager.agent_manager, "get_agent_config", return_value=fake_config
    ), patch.object(
        manager.agent_manager, "validate_execution"
    ), patch.object(
        manager.ai_runtime, "chat", side_effect=flaky_chat
    ), patch(
        "asyncio.sleep"
    ):
        completed = await manager.execute(execution.execution_id)

    assert completed.status == ExecutionStatus.COMPLETED
    assert completed.output_response == "ok"
    assert completed.retry_count == 2


@pytest.mark.asyncio
async def test_execute_failure_after_exhausted_retries(db_session, monkeypatch):
    manager = make_manager(db_session)
    execution = manager.create_execution(
        agent_id=1, input_messages=[{"role": "user", "content": "hi"}]
    )
    manager.submit(execution.execution_id)

    fake_agent = MagicMock()
    fake_agent.agent_model = MagicMock()
    fake_config = {"provider_id": 1, "model": "m1"}

    async def bad_chat(*, messages, provider_id, model, **kwargs):
        raise RuntimeError("rate limit exceeded")

    with patch.object(
        manager.agent_manager, "resolve_agent", return_value=fake_agent
    ), patch.object(
        manager.agent_manager, "get_agent_config", return_value=fake_config
    ), patch.object(
        manager.agent_manager, "validate_execution"
    ), patch.object(
        manager.ai_runtime, "chat", side_effect=bad_chat
    ), patch(
        "asyncio.sleep"
    ):
        completed = await manager.execute(execution.execution_id)

    assert completed.status == ExecutionStatus.FAILED
    assert "rate limit" in (completed.error_message or "")


def test_retry_policy_decisions(db_session):
    policy = RetryPolicy()
    assert policy.should_retry(0, RuntimeError("rate limit exceeded")) is True
    assert policy.should_retry(0, RuntimeError("server error 500")) is True
    assert policy.should_retry(0, ValueError("bad request")) is False
    assert policy.should_retry(0, RuntimeError("auth failure")) is False


def test_fallback_policy_no_fallback(db_session):
    policy = FallbackPolicy(db_session)
    fake_agent = MagicMock()
    result = policy.get_fallback(
        agent=fake_agent,
        primary_provider_id=1,
        primary_model="m1",
        failed_error=RuntimeError("boom"),
    )
    assert result is None
