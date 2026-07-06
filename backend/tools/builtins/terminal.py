"""Terminal Tool — execute shell commands."""

from typing import Any, Dict

from ..base import BaseTool, ToolMetadata
from ..context import ExecutionContext


class TerminalTool(BaseTool):
    """Execute shell commands in a controlled environment.

    Placeholder implementation — will be replaced with real sandboxed
    terminal execution in a future phase.
    """

    metadata = ToolMetadata(
        id="terminal.run",
        name="Terminal Run",
        description="Execute a shell command and return stdout, stderr, and exit code",
        version="0.1.0",
        category="terminal",
        input_schema={
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Shell command to execute",
                },
                "working_dir": {
                    "type": "string",
                    "description": "Working directory for the command",
                },
                "timeout_ms": {
                    "type": "integer",
                    "default": 30000,
                    "description": "Execution timeout in milliseconds",
                },
                "env": {
                    "type": "object",
                    "description": "Environment variables to set",
                    "default": {},
                },
            },
            "required": ["command"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "stdout": {"type": "string", "description": "Standard output"},
                "stderr": {"type": "string", "description": "Standard error"},
                "exit_code": {"type": "integer", "description": "Process exit code"},
                "execution_time_ms": {
                    "type": "integer",
                    "description": "Actual execution time",
                },
            },
        },
        timeout=60.0,
        supports_streaming=True,
        supports_cancellation=True,
        permissions=["terminal:execute"],
    )

    async def execute(
        self, input_data: Dict[str, Any], context: ExecutionContext
    ) -> Any:
        """Execute shell command (placeholder)."""
        context.check_cancellation()
        command = input_data["command"]
        context.log(f"TerminalTool: executing '{command}'")

        return {
            "stdout": f"[TerminalTool] Would execute: {command}",
            "stderr": "",
            "exit_code": 0,
            "execution_time_ms": 0,
        }


TOOL = TerminalTool()