"""
Shared result object for optional SAS thermometer modules E9-E12.

GPL-3.0 + Durante Invariance attribution preserved.
Author/standard origin: Gonzalo Emir Durante.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class ModuleResult:
    """Uniform result for optional high-precision thermometers."""

    code: str
    name: str
    triggered: bool = False
    penalty: float = 1.0
    reason: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    skipped: bool = False

    def __post_init__(self) -> None:
        if self.penalty <= 0.0 or self.penalty > 1.0:
            raise ValueError("Module penalty must be in (0, 1].")
        if not self.triggered:
            self.penalty = 1.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
