from __future__ import annotations

from risk_engine.rules import ALL_RULES
from risk_engine.types import RiskCheckResult, RiskContext


def run_risk_checks(ctx: RiskContext) -> RiskCheckResult:
    """Run every rule in priority order; return the first failure, or OK."""
    for rule in ALL_RULES:
        result = rule(ctx)
        if result is not None:
            return result
    return RiskCheckResult(allowed=True, code="OK", message="All risk checks passed.")
