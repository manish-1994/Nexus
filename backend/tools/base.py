"""Base tool interface and metadata definitions."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Dict, List, Optional
import json


@dataclass
class ToolMetadata:
    """Metadata describing a tool's capabilities and requirements."""

    id: str
    name: str
    description: str
    version: str
    category: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    timeout: float = 30.0
    supports_streaming: bool = False
    supports_cancellation: bool = True
    permissions: List[str] = field(default_factory=list)


class BaseTool(ABC):
    """Abstract base class for all tools.

    Subclasses must define the `metadata` class attribute and implement `execute()`.
    """

    # Class-level metadata (must be defined by subclasses)
    metadata: ToolMetadata

    @abstractmethod
    async def execute(
        self,
        input_data: Dict[str, Any],
        context: "ExecutionContext"
    ) -> Any:
        """Execute the tool synchronously (non-streaming).

        Args:
            input_data: Validated input matching input_schema
            context: Shared execution context with cancellation, logging, etc.

        Returns:
            Output data matching output_schema
        """
        pass

    async def execute_stream(
        self,
        input_data: Dict[str, Any],
        context: "ExecutionContext"
    ) -> AsyncGenerator[str, None]:
        """Execute the tool with streaming output.

        Default implementation yields a single JSON-encoded result.
        Override for true streaming tools.

        Args:
            input_data: Validated input matching input_schema
            context: Shared execution context

        Yields:
            JSON-encoded string chunks
        """
        result = await self.execute(input_data, context)
        yield json.dumps(result)

    def validate_input(self, input_data: Dict[str, Any]) -> None:
        """Validate input against input_schema.

        Args:
            input_data: Input to validate

        Raises:
            ValidationError: If input doesn't match schema
        """
        # Basic validation - can be extended with jsonschema
        required = self.metadata.input_schema.get("required", [])
        for field_name in required:
            if field_name not in input_data:
                raise ValueError(f"Missing required field: {field_name}")

    def validate_output(self, output_data: Any) -> None:
        """Validate output against output_schema.

        Args:
            output_data: Output to validate

        Raises:
            ValidationError: If output doesn't match schema
        """
        # Basic validation - can be extended with jsonschema
        pass


# Forward reference for type hints
from .context import ExecutionContext