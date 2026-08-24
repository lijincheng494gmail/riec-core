"""Cross-platform comparison hooks; values are configuration, not Core constants."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math

from .canonical import CanonicalModel, canonical_data
from .models import ArtifactOrigin


class ComparisonMode(str, Enum):
    EXACT_STRUCTURAL = "EXACT_STRUCTURAL"
    FLOAT_TOLERANT = "FLOAT_TOLERANT"
    STOCHASTIC_DISTRIBUTIONAL = "STOCHASTIC_DISTRIBUTIONAL"


@dataclass(frozen=True)
class FloatTolerancePolicy(CanonicalModel):
    policy_id: str
    policy_version: str
    absolute_tolerance: float
    relative_tolerance: float
    require_decision_invariance: bool
    origin: ArtifactOrigin = ArtifactOrigin.CONFIGURATION

    def __post_init__(self) -> None:
        if self.absolute_tolerance < 0 or self.relative_tolerance < 0:
            raise ValueError("tolerances cannot be negative")


def compare_exact(left: object, right: object) -> bool:
    return canonical_data(left) == canonical_data(right)


def compare_float(
    left: float,
    right: float,
    policy: FloatTolerancePolicy,
    *,
    left_action: str,
    right_action: str,
) -> bool:
    if policy.require_decision_invariance and left_action != right_action:
        return False
    return math.isclose(left, right, rel_tol=policy.relative_tolerance, abs_tol=policy.absolute_tolerance)


@dataclass(frozen=True)
class StochasticComparisonPolicy(CanonicalModel):
    policy_id: str
    policy_version: str
    paired_mean_tolerance: float
    require_identical_seed_set: bool
    require_decision_invariance: bool
    origin: ArtifactOrigin = ArtifactOrigin.CONFIGURATION


def compare_stochastic(
    left_values: tuple[float, ...],
    right_values: tuple[float, ...],
    left_seeds: tuple[int, ...],
    right_seeds: tuple[int, ...],
    policy: StochasticComparisonPolicy,
    *,
    left_action: str,
    right_action: str,
) -> bool:
    if not left_values or len(left_values) != len(right_values):
        return False
    if policy.require_identical_seed_set and left_seeds != right_seeds:
        return False
    if policy.require_decision_invariance and left_action != right_action:
        return False
    paired_mean = sum(abs(left - right) for left, right in zip(left_values, right_values, strict=True)) / len(left_values)
    return paired_mean <= policy.paired_mean_tolerance
