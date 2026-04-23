from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Literal

from impossible_ma.envelope import PossibilityEnvelope

Flavour = Literal[
    "disconnected_nma",
    "extreme_het",
    "cross_framing",
    "era_collision",
]
_VALID_FLAVOURS = (
    "disconnected_nma",
    "extreme_het",
    "cross_framing",
    "era_collision",
)


@dataclass
class PilotEnvelope:
    lower: float
    upper: float
    point: float | None
    min_info: str
    assumptions: dict[str, Any]
    case: str
    flavour: Flavour
    case_specific: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.flavour not in _VALID_FLAVOURS:
            raise ValueError(
                f"flavour must be one of {_VALID_FLAVOURS}, got {self.flavour!r}"
            )
        if self.lower > self.upper:
            raise ValueError(
                f"lower ({self.lower}) must be <= upper ({self.upper})"
            )
        if self.point is not None and not (self.lower <= self.point <= self.upper):
            raise ValueError(
                f"point {self.point} outside [{self.lower}, {self.upper}]"
            )
        if not isinstance(self.min_info, str) or not self.min_info:
            raise ValueError("min_info must be a non-empty string")
        if math.isinf(self.upper) and "unbounded" not in self.min_info:
            raise ValueError(
                "upper=inf requires 'unbounded' in min_info"
            )
        if math.isinf(self.lower) and "unbounded" not in self.min_info:
            raise ValueError(
                "lower=-inf requires 'unbounded' in min_info"
            )

    def to_possibility_envelope(self) -> PossibilityEnvelope:
        raise NotImplementedError(
            f"promotion requires adding {self.flavour!r} to the Literal "
            f"in src/impossible_ma/envelope.py and porting this pilot to src/"
        )
