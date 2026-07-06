"""Permission validation for tool execution."""

import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from .context import ExecutionContext

logger = logging.getLogger("tool_permissions")


class PermissionValidator:
    """Validates that an execution context has the required permissions for a tool.

    Currently uses a simple allowlist approach. Can be extended to:
    - Check agent-level permission grants
    - Check workspace-level scopes
    - Integrate with RBAC system
    """

    def __init__(self, db: Optional[Session] = None):
        self.db = db

    def validate(
        self,
        context: ExecutionContext,
        required_permissions: List[str],
    ) -> None:
        """Validate that the execution context has all required permissions.

        Args:
            context: The execution context
            required_permissions: List of permission scopes required by the tool

        Raises:
            PermissionError: If any required permission is not granted
        """
        if not required_permissions:
            return  # No permissions required

        # Get granted permissions for this context
        granted = self._get_granted_permissions(context)

        # Check each required permission
        # Handle wildcard permission ("*") which grants all
        if "*" in granted:
            missing = []
        else:
            missing = [p for p in required_permissions if p not in granted]

        if missing:
            raise PermissionError(
                f"Missing required permissions: {', '.join(missing)}. "
                f"Granted: {', '.join(granted) if granted else 'none'}"
            )

        logger.debug(
            "Permission check passed for exec=%s: required=%s granted=%s",
            context.execution_id,
            required_permissions,
            granted,
        )

    def _get_granted_permissions(self, context: ExecutionContext) -> List[str]:
        """Get the list of permissions granted to this execution context.

        Currently grants all permissions by default (development mode).
        In production, this would check:
        - Agent's configured permission set
        - Workspace-level scopes
        - User/role-based permissions

        Args:
            context: The execution context

        Returns:
            List of granted permission strings
        """
        # Development mode: grant all permissions
        # In production, this would query the database for agent/workspace permissions
        return ["*"]  # Wildcard grants everything

    def grant_permission(
        self,
        context: ExecutionContext,
        permission: str,
    ) -> None:
        """Grant a permission to an execution context (for future RBAC).

        Args:
            context: The execution context
            permission: The permission scope to grant
        """
        granted = context.metadata.setdefault("permissions", [])
        if permission not in granted:
            granted.append(permission)
            logger.debug(
                "Granted permission '%s' to exec=%s",
                permission,
                context.execution_id,
            )

    def revoke_permission(
        self,
        context: ExecutionContext,
        permission: str,
    ) -> None:
        """Revoke a permission from an execution context.

        Args:
            context: The execution context
            permission: The permission scope to revoke
        """
        granted = context.metadata.get("permissions", [])
        if permission in granted:
            granted.remove(permission)
            logger.debug(
                "Revoked permission '%s' from exec=%s",
                permission,
                context.execution_id,
            )