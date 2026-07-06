"""Python Tool — execute Python code in a sandboxed environment."""

from typing import Any, Dict

from ..base import BaseTool, ToolMetadata
from ..context import ExecutionContext


class PythonTool(BaseTool):
    """Execute Python code in a sandboxed environment.

    Placeholder implementation — will be replaced with real sandboxed
    Python execution (e.g., RestrictedPython, Docker container, or Pyodide)
    in a future phase.
    """

    metadata = ToolMetadata(
        id="python.execute",
        name="Python Execute",
        description="Execute Python code in a sandboxed environment and return the result",
        version="0.1.0",
        category="python",
        input_schema={
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code to execute",
                },
                "timeout_ms": {
                    "type": "integer",
                    "default": 10000,
                    "description": "Execution timeout in milliseconds",
                },
                "environment": {
                    "type": "object",
                    "description": "Pre-defined variables to inject",
                    "default": {},
                },
            },
            "required": ["code"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "stdout": {
                    "type": "string",
                    "description": "Standard output from execution",
                },
                "stderr": {
                    "type": "string",
                    "description": "Standard error from execution",
                },
                "result": {
                    "description": "Return value of the executed code (if any)",
                },
                "execution_time_ms": {
                    "type": "integer",
                    "description": "Actual execution time",
                },
            },
        },
        timeout=30.0,
        supports_streaming=False,
        supports_cancellation=True,
        permissions=["python:execute"],
    )

    async def execute(
        self, input_data: Dict[str, Any], context: ExecutionContext
    ) -> Any:
        """Execute Python code (placeholder)."""
        context.check_cancellation()
        code = input_data["code"]
        context.log(f"PythonTool: executing code ({len(code)} chars)")

        return {
            "stdout": f"[PythonTool] Would execute:\n{code[:200]}...",
            "stderr": "",
            "result": None,
            "execution_time_ms": 0,
        }


TOOL = PythonTool()