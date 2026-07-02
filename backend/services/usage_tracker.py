import logging
from typing import Optional
from datetime import datetime
from models.usage import Usage

logger = logging.getLogger("usage_tracker")


class UsageTracker:
    """Track AI usage and costs."""

    MODEL_COSTS = {
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4-turbo": {"input": 10.00, "output": 30.00},
        "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
        "llama-3.3-70b": {"input": 0.00, "output": 0.00},
        "llama-3.1-8b": {"input": 0.00, "output": 0.00},
        "mixtral-8x7b": {"input": 0.00, "output": 0.00},
        "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
        "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    }

    def __init__(self, db):
        self.db = db

    def track_usage(
        self,
        provider_id: int,
        model: str,
        request_type: str,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
    ) -> Usage:
        """Record usage for analytics."""
        total_tokens = (input_tokens or 0) + (output_tokens or 0)
        cost = self.estimate_cost(model, input_tokens or 0, output_tokens or 0)

        usage = Usage(
            provider_id=provider_id,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cost=cost,
            request_type=request_type,
            created_at=datetime.utcnow().isoformat(),
        )
        self.db.add(usage)
        self.db.commit()
        self.db.refresh(usage)
        return usage

    def estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost for a request."""
        model_costs = self.MODEL_COSTS.get(model.lower())
        if not model_costs:
            return 0.0
        input_cost = (input_tokens / 1_000_000) * model_costs["input"]
        output_cost = (output_tokens / 1_000_000) * model_costs["output"]
        return round(input_cost + output_cost, 6)

    def get_usage_stats(self, provider_id: int, limit: int = 100) -> list:
        """Get recent usage for a provider."""
        return (
            self.db.query(Usage)
            .filter(Usage.provider_id == provider_id)
            .order_by(Usage.created_at.desc())
            .limit(limit)
            .all()
        )
