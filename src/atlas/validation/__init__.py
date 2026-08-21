"""Published-control validation and the non-negotiable pre-design gate."""

from atlas.validation.validation_gate import (
    ValidationGateError,
    ValidationResult,
    evaluate_validation,
    require_validation_pass,
)

__all__ = [
    "ValidationGateError",
    "ValidationResult",
    "evaluate_validation",
    "require_validation_pass",
]
