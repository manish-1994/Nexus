"""Tool Registry — auto-discovers and registers tools from the builtins package."""

import importlib
import logging
import pkgutil
from typing import Dict, List, Optional

from .base import BaseTool, ToolMetadata

logger = logging.getLogger("tool_registry")


class ToolRegistry:
    """Auto-discovers and registers tools from backend/tools/builtins/.

    Tools are registered by their metadata.id and can be looked up
    by id, name, or category.
    """

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}  # id -> tool instance
        self._by_name: Dict[str, BaseTool] = {}  # name -> tool instance
        self._by_category: Dict[str, List[BaseTool]] = {}  # category -> tools

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, tool: BaseTool) -> None:
        """Register a tool instance.

        Args:
            tool: The tool instance to register

        Raises:
            ValueError: If a tool with the same id is already registered
        """
        meta = tool.metadata

        if meta.id in self._tools:
            raise ValueError(f"Tool '{meta.id}' is already registered")

        self._tools[meta.id] = tool
        self._by_name[meta.name] = tool
        self._by_category.setdefault(meta.category, []).append(tool)

        logger.info(
            "Registered tool: id=%s name=%s category=%s version=%s",
            meta.id,
            meta.name,
            meta.category,
            meta.version,
        )

    def unregister(self, tool_id: str) -> Optional[BaseTool]:
        """Remove a tool from the registry.

        Args:
            tool_id: The tool's unique identifier

        Returns:
            The removed tool, or None if not found
        """
        tool = self._tools.pop(tool_id, None)
        if tool:
            self._by_name.pop(tool.metadata.name, None)
            category_list = self._by_category.get(tool.metadata.category, [])
            if tool in category_list:
                category_list.remove(tool)
            logger.info("Unregistered tool: id=%s", tool_id)
        return tool

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def discover(self, package: str = "tools.builtins") -> None:
        """Auto-discover tools from a package.

        Scans the given package for modules that export a `TOOL` variable
        (a BaseTool instance) and registers them.

        Args:
            package: The dotted package path to scan (default: tools.builtins)
        """
        try:
            pkg = importlib.import_module(package)
        except ImportError as exc:
            logger.warning("Cannot discover tools from '%s': %s", package, exc)
            return

        if not hasattr(pkg, "__path__"):
            logger.warning("Package '%s' is not a package (no __path__)", package)
            return

        count = 0
        for _, module_name, _ in pkgutil.iter_modules(pkg.__path__):
            try:
                module = importlib.import_module(f"{package}.{module_name}")
                if hasattr(module, "TOOL"):
                    tool = module.TOOL
                    if isinstance(tool, BaseTool):
                        self.register(tool)
                        count += 1
                    else:
                        logger.warning(
                            "Module '%s.%s' has TOOL but it's not a BaseTool instance",
                            package,
                            module_name,
                        )
            except Exception as exc:
                logger.warning(
                    "Failed to load tool module '%s.%s': %s",
                    package,
                    module_name,
                    exc,
                )

        logger.info("Discovered %d tools from '%s'", count, package)

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def get(self, tool_id: str) -> Optional[BaseTool]:
        """Get a tool by its unique id.

        Args:
            tool_id: The tool's unique identifier (e.g., "browser.navigate")

        Returns:
            The tool instance, or None if not found
        """
        return self._tools.get(tool_id)

    def get_by_name(self, name: str) -> Optional[BaseTool]:
        """Get a tool by its human-readable name.

        Args:
            name: The tool's name (e.g., "Browser Navigate")

        Returns:
            The tool instance, or None if not found
        """
        return self._by_name.get(name)

    def list_tools(self, category: Optional[str] = None) -> List[BaseTool]:
        """List all registered tools, optionally filtered by category.

        Args:
            category: Optional category filter (e.g., "browser", "python")

        Returns:
            List of tool instances
        """
        if category:
            return self._by_category.get(category, [])
        return list(self._tools.values())

    def list_categories(self) -> List[str]:
        """List all registered tool categories."""
        return list(self._by_category.keys())

    def count(self) -> int:
        """Return the number of registered tools."""
        return len(self._tools)