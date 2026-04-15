from dataclasses import dataclass, field
from typing import Any, Literal

Case = Literal["k1", "missing_se", "adversarial"]
_VALID_CASES = ("k1", "missing_se", "adversarial")


@dataclass
class PossibilityEnvelope:
    lower: float
    upper: float
    point: float | None
    min_info: str
    assumptions: dict[str, Any]
    case: Case
    case_specific: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.case not in _VALID_CASES:
            raise ValueError(
                f"case must be one of {_VALID_CASES}, got {self.case!r}"
            )
        if self.lower > self.upper:
            raise ValueError(
                f"lower ({self.lower}) must be <= upper ({self.upper})"
            )


def validate_envelope(env: PossibilityEnvelope) -> None:
    if env.case not in _VALID_CASES:
        raise ValueError(f"invalid case: {env.case!r}")
    if env.lower > env.upper:
        raise ValueError(f"lower > upper: {env.lower} > {env.upper}")
    if env.point is not None and not (env.lower <= env.point <= env.upper):
        raise ValueError(
            f"point {env.point} outside [{env.lower}, {env.upper}]"
        )
    if not env.min_info or not isinstance(env.min_info, str):
        raise ValueError("min_info must be a non-empty string")
