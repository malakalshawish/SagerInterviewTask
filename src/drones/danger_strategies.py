from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, Optional


class DangerRule(Protocol):
    def check(
        self,
        *,
        height_m: Optional[float],
        horizontal_speed_mps: Optional[float],
    ) -> Optional[str]:
        """Return a reason string if dangerous, else None."""
        ...


@dataclass(frozen=True)
class HeightRule:
    threshold_m: float = 500.0

    def check(self, *, height_m: Optional[float], horizontal_speed_mps: Optional[float]) -> Optional[str]:
        if height_m is not None and height_m > self.threshold_m:
            return f"Altitude greater than {int(self.threshold_m)} meters"
        return None


@dataclass(frozen=True)
class SpeedRule:
    threshold_mps: float = 10.0

    def check(self, *, height_m: Optional[float], horizontal_speed_mps: Optional[float]) -> Optional[str]:
        if horizontal_speed_mps is not None and horizontal_speed_mps > self.threshold_mps:
            return f"Horizontal speed greater than {int(self.threshold_mps)} m/s"
        return None


class DangerClassifier:
    """Strategy context that applies a set of rules."""
    def __init__(self, rules: list[DangerRule]):
        self.rules = rules

    def classify(
        self,
        *,
        height_m: Optional[float],
        horizontal_speed_mps: Optional[float],
    ) -> list[str]:
        reasons: list[str] = []
        for rule in self.rules:
            reason = rule.check(height_m=height_m, horizontal_speed_mps=horizontal_speed_mps)
            if reason:
                reasons.append(reason)
        return reasons


def default_classifier() -> DangerClassifier:
    return DangerClassifier(rules=[HeightRule(), SpeedRule()])