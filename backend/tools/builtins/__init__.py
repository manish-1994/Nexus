"""Built-in tools for the Universal Tool Runtime.

Each module exports a `TOOL` variable (a BaseTool instance) that is
auto-discovered by ToolRegistry.discover().
"""

from .browser import BrowserTool
from .python import PythonTool
from .terminal import TerminalTool
from .file import FileTool
from .memory import MemoryTool
from .search import SearchTool

__all__ = [
    "BrowserTool",
    "PythonTool",
    "TerminalTool",
    "FileTool",
    "MemoryTool",
    "SearchTool",
]