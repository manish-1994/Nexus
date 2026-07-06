"""Tests for Universal Tool Runtime.

Covers:
- ToolRegistry auto-discovery and registration
- BaseTool interface and validation
- ToolManager execution lifecycle (execute, execute_stream, cancel)
- Permission validation
- Retry logic with exponential backoff
- Integration with AgentExecutionManager
- API endpoints
"""

import asyncio
import json
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from tools.base import BaseTool, ToolMetadata
from tools.context import ExecutionContext
from tools.manager import ToolManager, ToolExecutionConfig, ToolExecutionRecord
from tools.permissions import PermissionValidator
from tools.registry import ToolRegistry
from tools.schemas import ToolExecuteRequest, ToolExecuteResponse, ToolCancelRequest, ToolCancelResponse


# =============================================================================
# Test Fixtures
# =============================================================================

class MockTool(BaseTool):
    """Mock tool for testing."""
    
    metadata = ToolMetadata(
        id="test.mock",
        name="Mock Tool",
        description="A mock tool for testing",
        version="1.0.0",
        category="test",
        input_schema={
            "type": "object",
            "properties": {
                "value": {"type": "string"},
                "should_fail": {"type": "boolean", "default": False},
            },
            "required": ["value"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "result": {"type": "string"},
            },
        },
        timeout=10.0,
        supports_streaming=False,
        supports_cancellation=True,
        permissions=["test:mock"],
    )
    
    async def execute(self, input_data: dict, context: ExecutionContext) -> dict:
        context.check_cancellation()
        if input_data.get("should_fail"):
            raise ValueError("Mock tool failure")
        return {"result": f"processed: {input_data['value']}"}


class MockStreamingTool(BaseTool):
    """Mock streaming tool for testing."""
    
    metadata = ToolMetadata(
        id="test.streaming",
        name="Mock Streaming Tool",
        description="A mock streaming tool for testing",
        version="1.0.0",
        category="test",
        input_schema={
            "type": "object",
            "properties": {
                "chunks": {"type": "integer", "default": 3},
            },
        },
        output_schema={
            "type": "object",
            "properties": {
                "chunk": {"type": "string"},
            },
        },
        timeout=10.0,
        supports_streaming=True,
        supports_cancellation=True,
        permissions=["test:streaming"],
    )
    
    async def execute(self, input_data: dict, context: ExecutionContext) -> dict:
        """Default execute implementation for streaming tool."""
        chunks = input_data.get("chunks", 3)
        results = []
        for i in range(chunks):
            context.check_cancellation()
            await asyncio.sleep(0.01)
            results.append(f"chunk-{i}")
        return {"chunks": results}
    
    async def execute_stream(self, input_data: dict, context: ExecutionContext):
        chunks = input_data.get("chunks", 3)
        for i in range(chunks):
            context.check_cancellation()
            await asyncio.sleep(0.01)
            yield json.dumps({"chunk": f"chunk-{i}"})


@pytest.fixture
def mock_tool():
    return MockTool()


@pytest.fixture
def mock_streaming_tool():
    return MockStreamingTool()


@pytest.fixture
def registry():
    reg = ToolRegistry()
    reg.register(MockTool())
    reg.register(MockStreamingTool())
    return reg


@pytest.fixture
def permission_validator():
    return PermissionValidator()


@pytest.fixture
def tool_manager(registry, permission_validator):
    return ToolManager(
        registry=registry,
        permission_validator=permission_validator,
        config=ToolExecutionConfig(max_retries=2, base_delay=0.01),
    )


@pytest.fixture
def execution_context():
    return ExecutionContext(
        execution_id="test-exec-123",
        agent_id=1,
        conversation_id=10,
        workspace_id=5,
    )


# =============================================================================
# ToolRegistry Tests
# =============================================================================

class TestToolRegistry:
    """Tests for ToolRegistry auto-discovery and registration."""
    
    def test_register_and_get(self, registry):
        tool = registry.get("test.mock")
        assert tool is not None
        assert tool.metadata.id == "test.mock"
        assert tool.metadata.name == "Mock Tool"
    
    def test_register_duplicate_raises(self, registry):
        with pytest.raises(ValueError, match="already registered"):
            registry.register(MockTool())
    
    def test_unregister(self, registry):
        removed = registry.unregister("test.mock")
        assert removed is not None
        assert registry.get("test.mock") is None
        assert registry.count() == 1
    
    def test_unregister_not_found(self, registry):
        removed = registry.unregister("nonexistent")
        assert removed is None
    
    def test_get_by_name(self, registry):
        tool = registry.get_by_name("Mock Tool")
        assert tool is not None
        assert tool.metadata.id == "test.mock"
    
    def test_list_tools(self, registry):
        tools = registry.list_tools()
        assert len(tools) == 2
    
    def test_list_tools_by_category(self, registry):
        tools = registry.list_tools(category="test")
        assert len(tools) == 2
        
        tools = registry.list_tools(category="nonexistent")
        assert len(tools) == 0
    
    def test_list_categories(self, registry):
        categories = registry.list_categories()
        assert "test" in categories
    
    def test_count(self, registry):
        assert registry.count() == 2
    
    def test_discover_builtins(self):
        """Test auto-discovery of built-in tools."""
        reg = ToolRegistry()
        reg.discover("tools.builtins")
        # Should discover at least the 6 placeholder tools
        assert reg.count() >= 6
        categories = reg.list_categories()
        assert "browser" in categories
        assert "python" in categories
        assert "terminal" in categories
        assert "file" in categories
        assert "memory" in categories
        assert "search" in categories


# =============================================================================
# BaseTool Tests
# =============================================================================

class TestBaseTool:
    """Tests for BaseTool interface and validation."""
    
    def test_validate_input_success(self, mock_tool):
        mock_tool.validate_input({"value": "test"})
    
    def test_validate_input_missing_required(self, mock_tool):
        with pytest.raises(ValueError, match="Missing required field: value"):
            mock_tool.validate_input({})
    
    def test_validate_output_noop(self, mock_tool):
        # Default implementation does nothing
        mock_tool.validate_output({"result": "ok"})
        mock_tool.validate_output("anything")
    
    @pytest.mark.asyncio
    async def test_execute_stream_default(self, mock_tool, execution_context):
        """Default execute_stream yields single JSON result."""
        chunks = []
        async for chunk in mock_tool.execute_stream({"value": "test"}, execution_context):
            chunks.append(chunk)
        assert len(chunks) == 1
        data = json.loads(chunks[0])
        assert data["result"] == "processed: test"


# =============================================================================
# PermissionValidator Tests
# =============================================================================

class TestPermissionValidator:
    """Tests for permission validation."""
    
    def test_validate_no_permissions_required(self, permission_validator, execution_context):
        # Should not raise
        permission_validator.validate(execution_context, [])
    
    def test_validate_wildcard_grants_all(self, permission_validator, execution_context):
        # Development mode grants "*" which matches everything
        permission_validator.validate(execution_context, ["any:permission", "another:perm"])
    
    def test_validate_specific_permission_granted(self, permission_validator, execution_context):
        permission_validator.grant_permission(execution_context, "test:mock")
        permission_validator.validate(execution_context, ["test:mock"])
    
    def test_validate_missing_permission_raises(self, permission_validator, execution_context):
        # Create a validator that doesn't grant wildcard
        class StrictValidator(PermissionValidator):
            def _get_granted_permissions(self, context):
                return ["test:mock"]  # Only grant test:mock
        
        strict = StrictValidator()
        strict.validate(execution_context, ["test:mock"])  # OK
        
        with pytest.raises(PermissionError, match="Missing required permissions"):
            strict.validate(execution_context, ["other:perm"])
    
    def test_revoke_permission(self, permission_validator, execution_context):
        permission_validator.grant_permission(execution_context, "test:mock")
        permission_validator.revoke_permission(execution_context, "test:mock")
        
        class StrictValidator(PermissionValidator):
            def _get_granted_permissions(self, context):
                return context.metadata.get("permissions", [])
        
        strict = StrictValidator()
        with pytest.raises(PermissionError):
            strict.validate(execution_context, ["test:mock"])


# =============================================================================
# ToolManager Tests
# =============================================================================

class TestToolManager:
    """Tests for ToolManager execution lifecycle."""
    
    @pytest.mark.asyncio
    async def test_execute_success(self, tool_manager, execution_context):
        result = await tool_manager.execute(
            tool_id="test.mock",
            input_data={"value": "hello"},
            context=execution_context,
        )
        assert result == {"result": "processed: hello"}
    
    @pytest.mark.asyncio
    async def test_execute_tool_not_found(self, tool_manager, execution_context):
        with pytest.raises(ValueError, match="not found"):
            await tool_manager.execute(
                tool_id="nonexistent",
                input_data={},
                context=execution_context,
            )
    
    @pytest.mark.asyncio
    async def test_execute_permission_denied(self, tool_manager, execution_context):
        class StrictValidator(PermissionValidator):
            def _get_granted_permissions(self, context):
                return []  # Grant nothing
        
        strict_manager = ToolManager(
            registry=tool_manager.registry,
            permission_validator=StrictValidator(),
        )
        
        with pytest.raises(PermissionError, match="Missing required permissions"):
            await strict_manager.execute(
                tool_id="test.mock",
                input_data={"value": "test"},
                context=execution_context,
            )
    
    @pytest.mark.asyncio
    async def test_execute_input_validation_failure(self, tool_manager, execution_context):
        with pytest.raises(ValueError, match="Missing required field: value"):
            await tool_manager.execute(
                tool_id="test.mock",
                input_data={},  # Missing required 'value'
                context=execution_context,
            )
    
    @pytest.mark.asyncio
    async def test_execute_tool_failure(self, tool_manager, execution_context):
        with pytest.raises(ValueError, match="Mock tool failure"):
            await tool_manager.execute(
                tool_id="test.mock",
                input_data={"value": "test", "should_fail": True},
                context=execution_context,
            )
    
    @pytest.mark.asyncio
    async def test_execute_retry_then_success(self, tool_manager, execution_context):
        """Test retry logic with eventual success."""
        call_count = 0
        
        class FlakyTool(BaseTool):
            metadata = ToolMetadata(
                id="test.flaky",
                name="Flaky Tool",
                description="Fails twice then succeeds",
                version="1.0.0",
                category="test",
                input_schema={"type": "object", "properties": {}},
                output_schema={"type": "object", "properties": {}},
                timeout=10.0,
            )
            
            async def execute(self, input_data, context):
                nonlocal call_count
                call_count += 1
                if call_count < 3:
                    raise ConnectionError("Temporary failure")
                return {"success": True}
        
        tool_manager.registry.register(FlakyTool())
        
        result = await tool_manager.execute(
            tool_id="test.flaky",
            input_data={},
            context=execution_context,
        )
        assert result == {"success": True}
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_execute_exhausted_retries(self, tool_manager, execution_context):
        """Test that retries are exhausted and error is raised."""
        class AlwaysFailsTool(BaseTool):
            metadata = ToolMetadata(
                id="test.always_fails",
                name="Always Fails Tool",
                description="Always fails",
                version="1.0.0",
                category="test",
                input_schema={"type": "object", "properties": {}},
                output_schema={"type": "object", "properties": {}},
                timeout=10.0,
            )
            
            async def execute(self, input_data, context):
                raise ConnectionError("Permanent failure")
        
        tool_manager.registry.register(AlwaysFailsTool())
        
        with pytest.raises(ConnectionError, match="Permanent failure"):
            await tool_manager.execute(
                tool_id="test.always_fails",
                input_data={},
                context=execution_context,
            )
    
    @pytest.mark.asyncio
    async def test_execute_stream_success(self, tool_manager, execution_context):
        chunks = []
        async for chunk in tool_manager.execute_stream(
            tool_id="test.streaming",
            input_data={"chunks": 2},
            context=execution_context,
        ):
            chunks.append(chunk)
        
        assert len(chunks) == 2
        data1 = json.loads(chunks[0])
        data2 = json.loads(chunks[1])
        assert data1["chunk"] == "chunk-0"
        assert data2["chunk"] == "chunk-1"
    
    @pytest.mark.asyncio
    async def test_execute_stream_tool_not_streaming(self, tool_manager, execution_context):
        with pytest.raises(ValueError, match="does not support streaming"):
            async for _ in tool_manager.execute_stream(
                tool_id="test.mock",  # Not a streaming tool
                input_data={"value": "test"},
                context=execution_context,
            ):
                pass
    
    @pytest.mark.asyncio
    async def test_cancel_execution(self, tool_manager, execution_context):
        # Start a long-running execution
        
        class LongRunningTool(BaseTool):
            metadata = ToolMetadata(
                id="test.long",
                name="Long Running Tool",
                description="Takes a while",
                version="1.0.0",
                category="test",
                input_schema={"type": "object", "properties": {}},
                output_schema={"type": "object", "properties": {}},
                timeout=60.0,
                supports_cancellation=True,
            )
            
            async def execute(self, input_data, context):
                # Check for cancellation periodically
                for _ in range(100):
                    context.check_cancellation()
                    await asyncio.sleep(0.1)
                return {"done": True}
        
        tool_manager.registry.register(LongRunningTool())
        
        # Execute in background
        task = asyncio.create_task(
            tool_manager.execute("test.long", {}, execution_context)
        )
        
        # Give it time to start
        await asyncio.sleep(0.05)
        
        # Cancel it
        active = tool_manager.get_active_executions()
        assert len(active) == 1
        
        cancelled = tool_manager.cancel(active[0])
        assert cancelled is True
        
        # Task should be cancelled
        with pytest.raises(asyncio.CancelledError):
            await task
    
    @pytest.mark.asyncio
    async def test_cancel_nonexistent(self, tool_manager):
        cancelled = tool_manager.cancel("nonexistent")
        assert cancelled is False
    
    @pytest.mark.asyncio
    async def test_cancel_non_cancellable_tool(self, tool_manager, execution_context):
        class NonCancellableTool(BaseTool):
            metadata = ToolMetadata(
                id="test.non_cancellable",
                name="Non Cancellable Tool",
                description="Cannot be cancelled",
                version="1.0.0",
                category="test",
                input_schema={"type": "object", "properties": {}},
                output_schema={"type": "object", "properties": {}},
                timeout=10.0,
                supports_cancellation=False,
            )
            
            async def execute(self, input_data, context):
                await asyncio.sleep(10)
                return {"done": True}
        
        tool_manager.registry.register(NonCancellableTool())
        
        task = asyncio.create_task(
            tool_manager.execute("test.non_cancellable", {}, execution_context)
        )
        await asyncio.sleep(0.05)
        
        active = tool_manager.get_active_executions()
        cancelled = tool_manager.cancel(active[0])
        assert cancelled is False  # Tool doesn't support cancellation
        
        # Clean up
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    
    def test_get_active_executions(self, tool_manager):
        assert tool_manager.get_active_executions() == []
    
    def test_get_execution_status(self, tool_manager):
        assert tool_manager.get_execution_status("nonexistent") is None


# =============================================================================
# ExecutionContext Tests
# =============================================================================

class TestExecutionContext:
    """Tests for shared ExecutionContext."""
    
    def test_is_cancelled_false(self, execution_context):
        assert execution_context.is_cancelled() is False
    
    def test_is_cancelled_true(self, execution_context):
        execution_context.cancel_event.set()
        assert execution_context.is_cancelled() is True
    
    def test_check_cancellation_raises(self, execution_context):
        execution_context.cancel_event.set()
        with pytest.raises(asyncio.CancelledError):
            execution_context.check_cancellation()
    
    def test_check_cancellation_no_raise(self, execution_context):
        # Should not raise
        execution_context.check_cancellation()
    
    def test_log(self, execution_context, caplog):
        import logging
        # Set up caplog to capture the execution logger
        caplog.set_level(logging.INFO, logger="execution")
        execution_context.log("Test message")
        assert "Test message" in caplog.text
        assert "test-exec-123" in caplog.text
        assert "agent=1" in caplog.text


# =============================================================================
# ToolManager + AgentExecutionManager Integration Tests
# =============================================================================

class TestToolRuntimeIntegration:
    """Tests for ToolManager integration with AgentExecutionManager."""
    
    @pytest.fixture
    def db_session(self):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.pool import StaticPool
        from database import Base
        
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()
    
    @pytest.fixture
    def execution_manager(self, db_session):
        from services.execution_manager import AgentExecutionManager
        from models.agent import Agent
        from models.provider import Provider, ProviderType, ProviderStatus
        from models.model import Model
        
        # Create test data
        provider = Provider(
            name="Test Provider",
            type=ProviderType.OPENAI_COMPATIBLE,
            base_url="http://localhost:1234",
            health_status=ProviderStatus.ACTIVE,
        )
        db_session.add(provider)
        db_session.commit()
        
        model = Model(
            provider_id=provider.id,
            name="test-model",
            display_name="Test Model",
        )
        db_session.add(model)
        db_session.commit()
        
        agent = Agent(
            name="Test Agent",
            prompt_template="You are a test agent.",
            provider_id=provider.id,
            preferred_model_id=model.id,
            temperature=0.7,
        )
        db_session.add(agent)
        db_session.commit()
        
        return AgentExecutionManager(db_session)
    
    @pytest.mark.asyncio
    async def test_execute_tool_integration(self, execution_manager, db_session):
        """Test AgentExecutionManager.execute_tool() integration."""
        from models.execution import Execution, ExecutionStatus
        
        # Create and submit execution
        execution = execution_manager.create_execution(
            agent_id=1,
            input_messages=[{"role": "user", "content": "test"}],
        )
        execution_manager.submit(execution.execution_id)
        
        # Transition to RUNNING state (required for tool execution)
        execution_manager._transition_status(execution, ExecutionStatus.RUNNING)
        
        # Execute a tool
        result = await execution_manager.execute_tool(
            execution_id=execution.execution_id,
            tool_id="browser.navigate",
            input_data={"url": "https://example.com", "extract": "text"},
        )
        
        assert result is not None
        assert "content" in result
        assert "title" in result
        
        # Verify tool call was recorded
        db_session.refresh(execution)
        assert execution.tool_calls is not None
        assert len(execution.tool_calls) == 1
        assert execution.tool_calls[0]["tool_id"] == "browser.navigate"
    
    @pytest.mark.asyncio
    async def test_execute_tool_invalid_state(self, execution_manager, db_session):
        """Test execute_tool fails in invalid execution state."""
        from models.execution import Execution, ExecutionStatus
        
        execution = execution_manager.create_execution(agent_id=1)
        # Don't submit - stays in IDLE
        
        with pytest.raises(ValueError, match="Cannot execute tool in execution status"):
            await execution_manager.execute_tool(
                execution_id=execution.execution_id,
                tool_id="browser.navigate",
                input_data={"url": "https://example.com"},
            )
    
    @pytest.mark.asyncio
    async def test_execute_tool_stream_integration(self, execution_manager, db_session):
        """Test AgentExecutionManager.execute_tool_stream() integration."""
        from models.execution import Execution, ExecutionStatus
        
        execution = execution_manager.create_execution(
            agent_id=1,
            input_messages=[{"role": "user", "content": "test"}],
        )
        execution_manager.submit(execution.execution_id)
        
        # Transition to RUNNING state (required for tool execution)
        execution_manager._transition_status(execution, ExecutionStatus.RUNNING)
        
        chunks = []
        async for chunk in execution_manager.execute_tool_stream(
            execution_id=execution.execution_id,
            tool_id="terminal.run",
            input_data={"command": "echo hello", "working_dir": "/tmp"},
        ):
            chunks.append(chunk)
        
        assert len(chunks) > 0
        
        # Verify tool call was recorded
        db_session.refresh(execution)
        assert execution.tool_calls is not None
        assert len(execution.tool_calls) == 1
    
    def test_list_available_tools(self, execution_manager):
        """Test listing tools available to agents."""
        tools = execution_manager.list_available_tools()
        assert len(tools) >= 6
        
        # Check structure
        for tool in tools:
            assert "id" in tool
            assert "name" in tool
            assert "description" in tool
            assert "category" in tool
            assert "input_schema" in tool
            assert "supports_streaming" in tool
            assert "permissions" in tool
    
    def test_list_available_tools_by_category(self, execution_manager):
        browser_tools = execution_manager.list_available_tools(category="browser")
        assert len(browser_tools) >= 1
        assert all(t["category"] == "browser" for t in browser_tools)


# =============================================================================
# API Endpoint Tests
# =============================================================================

class TestToolAPI:
    """Tests for Tool Runtime API endpoints."""
    
    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from app import app
        from database import get_db
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.pool import StaticPool
        from database import Base
        from config import settings
        
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=engine)
        TestingSessionLocal = sessionmaker(bind=engine)
        
        def override_get_db():
            try:
                yield TestingSessionLocal()
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        with TestClient(app) as test_client:
            yield test_client
        app.dependency_overrides.clear()
    
    def test_list_tools(self, client):
        response = client.get("/api/v1/tools")
        assert response.status_code == 200
        tools = response.json()
        assert isinstance(tools, list)
        assert len(tools) >= 6
    
    def test_list_tools_by_category(self, client):
        response = client.get("/api/v1/tools?category=browser")
        assert response.status_code == 200
        tools = response.json()
        assert all(t["metadata"]["category"] == "browser" for t in tools)
    
    def test_list_categories(self, client):
        response = client.get("/api/v1/tools/categories")
        assert response.status_code == 200
        categories = response.json()
        assert isinstance(categories, list)
        assert "browser" in categories
        assert "python" in categories
    
    def test_inspect_tool(self, client):
        response = client.get("/api/v1/tools/browser.navigate")
        assert response.status_code == 200
        tool = response.json()
        assert tool["metadata"]["id"] == "browser.navigate"
        assert "input_schema" in tool["metadata"]
        assert "output_schema" in tool["metadata"]
    
    def test_inspect_tool_not_found(self, client):
        response = client.get("/api/v1/tools/nonexistent")
        assert response.status_code == 404
    
    def test_execute_tool(self, client):
        response = client.post(
            "/api/v1/tools/browser.navigate/execute",
            json={
                "execution_id": "test-exec-1",
                "agent_id": 1,
                "input_data": {"url": "https://example.com", "extract": "text"},
            },
        )
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "completed"
        assert result["output"] is not None
        assert "content" in result["output"]
    
    def test_execute_tool_not_found(self, client):
        response = client.post(
            "/api/v1/tools/nonexistent/execute",
            json={
                "execution_id": "test-exec-1",
                "agent_id": 1,
                "input_data": {},
            },
        )
        assert response.status_code == 404
    
    def test_execute_tool_invalid_input(self, client):
        response = client.post(
            "/api/v1/tools/browser.navigate/execute",
            json={
                "execution_id": "test-exec-1",
                "agent_id": 1,
                "input_data": {},  # Missing required 'url'
            },
        )
        assert response.status_code == 400
    
    def test_cancel_tool_execution(self, client):
        # First start an execution (we can't easily test active cancellation
        # without a long-running tool, so test the not_found case)
        response = client.post(
            "/api/v1/tools/cancel",
            json={"execution_id": "nonexistent"},
        )
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "not_found"
    
    def test_list_active_executions(self, client):
        response = client.get("/api/v1/tools/executions/active")
        assert response.status_code == 200
        active = response.json()
        assert isinstance(active, list)


# =============================================================================
# Schema Tests
# =============================================================================

class TestToolSchemas:
    """Tests for Pydantic schemas."""
    
    def test_tool_execute_request(self):
        req = ToolExecuteRequest(
            execution_id="test-123",
            agent_id=1,
            input_data={"key": "value"},
        )
        assert req.execution_id == "test-123"
        assert req.agent_id == 1
        assert req.input_data == {"key": "value"}
    
    def test_tool_execute_response(self):
        resp = ToolExecuteResponse(
            execution_id="test-123",
            tool_id="test.tool",
            status="completed",
            output={"result": "ok"},
        )
        assert resp.status == "completed"
        assert resp.output == {"result": "ok"}
    
    def test_tool_cancel_request(self):
        req = ToolCancelRequest(execution_id="test-123")
        assert req.execution_id == "test-123"
    
    def test_tool_cancel_response(self):
        resp = ToolCancelResponse(
            execution_id="test-123",
            status="cancelled",
        )
        assert resp.status == "cancelled"


# =============================================================================
# ToolExecutionConfig Tests
# =============================================================================

class TestToolExecutionConfig:
    """Tests for ToolExecutionConfig."""
    
    def test_defaults(self):
        config = ToolExecutionConfig()
        assert config.max_retries == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 30.0
        assert config.exponential_base == 2.0
    
    def test_custom(self):
        config = ToolExecutionConfig(
            max_retries=5,
            base_delay=0.5,
            max_delay=60.0,
            exponential_base=3.0,
        )
        assert config.max_retries == 5
        assert config.base_delay == 0.5
        assert config.max_delay == 60.0
        assert config.exponential_base == 3.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])