"""Retry and fallback policies for agent execution.

Provides exponential backoff retry for transient provider errors
and automatic provider fallback when the primary provider fails.
"""

import asyncio
import logging
from typing import Dict, List, Optional

from models.agent import Agent
from models.provider import Provider, ProviderStatus
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Error patterns that indicate a transient (retryable) failure
RETRYABLE_ERROR_PATTERNS = [
    "rate limit",
    "rate_limit",
    "too many requests",
    "429",
    "timeout",
    "timed out",
    "service unavailable",
    "503",
    "bad gateway",
    "502",
    "gateway timeout",
    "504",
    "internal server error",
    "500",
    "connection",
    "network",
    "reset by peer",
    "broken pipe",
    "temporary",
    "overloaded",
    "capacity",
    "try again",
]

# Error patterns that indicate a non-retryable (permanent) failure
NON_RETRYABLE_ERROR_PATTERNS = [
    "unauthorized",
    "401",
    "forbidden",
    "403",
    "invalid api key",
    "authentication",
    "auth failure",
    "auth error",
    "bad request",
    "400",
    "not found",
    "404",
    "method not allowed",
    "405",
    "payload too large",
    "413",
    "unsupported media type",
    "415",
    "quota",
    "billing",
    "insufficient",
]


class RetryPolicy:
    """Determines whether and how to retry a failed execution.

    Uses exponential backoff with jitter for retry delays.
    Only retries on transient errors (rate limits, timeouts, 5xx).
    Does NOT retry on auth errors (401, 403) or bad requests (400).
    """

    def __init__(
        self,
        max_retries: int = 3,
        base_delay_ms: int = 1000,
        backoff_factor: float = 2.0,
        max_delay_ms: int = 30000,
    ):
        self.max_retries = max_retries
        self.base_delay_ms = base_delay_ms
        self.backoff_factor = backoff_factor
        self.max_delay_ms = max_delay_ms

    def should_retry(self, attempt: int, error: Exception) -> bool:
        """Determine if a retry is warranted based on attempt count and error type.

        Args:
            attempt: Zero-based attempt number (0 = first attempt already failed)
            error: The exception that caused the failure

        Returns:
            True if another retry should be attempted
        """
        if attempt >= self.max_retries:
            logger.debug("Max retries (%d) exhausted", self.max_retries)
            return False

        error_str = str(error).lower()

        # Check non-retryable patterns first (they take precedence)
        for pattern in NON_RETRYABLE_ERROR_PATTERNS:
            if pattern in error_str:
                logger.info(
                    "Non-retryable error detected (pattern: '%s'), skipping retry",
                    pattern,
                )
                return False

        # Check retryable patterns
        for pattern in RETRYABLE_ERROR_PATTERNS:
            if pattern in error_str:
                logger.info(
                    "Retryable error detected (pattern: '%s'), attempt %d/%d",
                    pattern,
                    attempt + 1,
                    self.max_retries,
                )
                return True

        # Unknown errors: retry once, then give up
        if attempt == 0:
            logger.info("Unknown error type, allowing one retry attempt")
            return True

        logger.info("Unknown error type, retries exhausted")
        return False

    def delay_ms(self, attempt: int) -> int:
        """Calculate delay before next retry using exponential backoff.

        Args:
            attempt: Zero-based attempt number

        Returns:
            Delay in milliseconds
        """
        delay = self.base_delay_ms * (self.backoff_factor**attempt)
        # Add jitter: +/- 25%
        import random

        jitter = delay * 0.25 * (random.random() * 2 - 1)
        delay = int(delay + jitter)
        return min(delay, self.max_delay_ms)

    async def wait_before_retry(self, attempt: int) -> None:
        """Sleep for the calculated backoff delay."""
        delay = self.delay_ms(attempt)
        logger.debug("Waiting %d ms before retry attempt %d", delay, attempt + 1)
        await asyncio.sleep(delay / 1000.0)


class FallbackPolicy:
    """Determines fallback provider when the primary provider fails.

    Priority:
    1. Agent's explicitly configured fallback (if available)
    2. Any other active provider with the same model
    3. Any active provider with any model
    """

    def __init__(self, db: Session):
        self.db = db

    def get_fallback(
        self,
        agent: Agent,
        primary_provider_id: int,
        primary_model: str,
        failed_error: Exception,
    ) -> Optional[Dict]:
        """Find a fallback provider and model.

        Args:
            agent: The agent being executed
            primary_provider_id: The provider that failed
            primary_model: The model that was being used
            failed_error: The exception that caused the failure

        Returns:
            Dict with 'provider_id' and 'model' keys, or None if no fallback available
        """
        error_str = str(failed_error).lower()

        # Don't fallback for auth errors — those are configuration problems
        for pattern in NON_RETRYABLE_ERROR_PATTERNS:
            if pattern in error_str:
                logger.info("Non-retryable error, skipping provider fallback")
                return None

        # Strategy 1: Try any other active provider with the same model
        same_model_provider = (
            self.db.query(Provider)
            .filter(
                Provider.id != primary_provider_id,
                Provider.health_status == ProviderStatus.ACTIVE,
            )
            .first()
        )

        if same_model_provider:
            # Check if this provider has the same model available
            from models.model import Model

            model_exists = (
                self.db.query(Model)
                .filter(
                    Model.provider_id == same_model_provider.id,
                    Model.name == primary_model,
                    Model.is_active == True,
                )
                .first()
            )

            if model_exists:
                logger.info(
                    "Fallback: using provider '%s' (id=%d) with same model '%s'",
                    same_model_provider.name,
                    same_model_provider.id,
                    primary_model,
                )
                return {
                    "provider_id": same_model_provider.id,
                    "model": primary_model,
                }

        # Strategy 2: Try any active provider (different model)
        any_provider = (
            self.db.query(Provider)
            .filter(
                Provider.id != primary_provider_id,
                Provider.health_status == ProviderStatus.ACTIVE,
            )
            .first()
        )

        if any_provider:
            # Get the first active model for this provider
            from models.model import Model

            first_model = (
                self.db.query(Model)
                .filter(
                    Model.provider_id == any_provider.id,
                    Model.is_active == True,
                )
                .first()
            )

            if first_model:
                logger.info(
                    "Fallback: using provider '%s' (id=%d) with model '%s'",
                    any_provider.name,
                    any_provider.id,
                    first_model.name,
                )
                return {
                    "provider_id": any_provider.id,
                    "model": first_model.name,
                }

        logger.warning("No fallback provider available")
        return None
