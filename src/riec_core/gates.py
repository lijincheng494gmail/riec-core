"""Non-compensatory gate result and eligibility projection."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import re

from .canonical import CanonicalModel, canonical_checksum
from .models import ArtifactOrigin, EligibilityState, GateState, Repairability


_SHA256 = re.compile(r"^[a-f0-9]{64}$")


@dataclass(frozen=True)
class GateResult(CanonicalModel):
    gate_id: str
    gate_version: str
    state: GateState
    reason_code: str
    evidence_refs: tuple[str, ...]
    affected_actions: tuple[str, ...]
    repairability: Repairability
    timestamp: datetime
    config_hash: str
    permitted_actions: tuple[str, ...] = ()
    conditions: tuple[str, ...] = ()
    origin: ArtifactOrigin = ArtifactOrigin.RUNTIME_RESULT

    def __post_init__(self) -> None:
        if not self.gate_id or not self.gate_version or not self.reason_code:
            raise ValueError("gate identity, version, and reason code are required")
        if self.timestamp.tzinfo is None:
            raise ValueError("gate timestamp must be timezone-aware")
        if not _SHA256.fullmatch(self.config_hash):
            raise ValueError("config_hash must be SHA-256")
        if self.state is GateState.WARN and (not self.permitted_actions or not self.conditions):
            raise ValueError("WARN requires permitted actions and explicit conditions")


@dataclass(frozen=True)
class GateDecision(CanonicalModel):
    action: str
    eligibility: EligibilityState
    blocking_gate_ids: tuple[str, ...]
    warning_gate_ids: tuple[str, ...]
    reason_codes: tuple[str, ...]
    gate_snapshot_hash: str


class GateEngine:
    """Projects gate results to an action set without an aggregate score."""

    @staticmethod
    def evaluate(results: tuple[GateResult, ...], action: str) -> GateDecision:
        relevant = tuple(
            result for result in results if "*" in result.affected_actions or action in result.affected_actions
        )
        snapshot = canonical_checksum(results)
        if not relevant:
            return GateDecision(
                action=action,
                eligibility=EligibilityState.NOT_EVALUABLE,
                blocking_gate_ids=(),
                warning_gate_ids=(),
                reason_codes=("CORE.GATE.NO_RELEVANT_RESULT",),
                gate_snapshot_hash=snapshot,
            )

        failures = tuple(result for result in relevant if result.state is GateState.FAIL)
        if failures:
            return GateDecision(
                action=action,
                eligibility=EligibilityState.INELIGIBLE,
                blocking_gate_ids=tuple(result.gate_id for result in failures),
                warning_gate_ids=(),
                reason_codes=tuple(result.reason_code for result in failures),
                gate_snapshot_hash=snapshot,
            )

        unknown = tuple(result for result in relevant if result.state is GateState.NOT_EVALUABLE)
        if unknown:
            return GateDecision(
                action=action,
                eligibility=EligibilityState.NOT_EVALUABLE,
                blocking_gate_ids=tuple(result.gate_id for result in unknown),
                warning_gate_ids=(),
                reason_codes=tuple(result.reason_code for result in unknown),
                gate_snapshot_hash=snapshot,
            )

        warnings = tuple(result for result in relevant if result.state is GateState.WARN)
        if warnings:
            forbidden = tuple(result for result in warnings if action not in result.permitted_actions)
            if forbidden:
                return GateDecision(
                    action=action,
                    eligibility=EligibilityState.INELIGIBLE,
                    blocking_gate_ids=tuple(result.gate_id for result in forbidden),
                    warning_gate_ids=tuple(result.gate_id for result in warnings),
                    reason_codes=tuple(result.reason_code for result in warnings),
                    gate_snapshot_hash=snapshot,
                )
            return GateDecision(
                action=action,
                eligibility=EligibilityState.CONDITIONALLY_ELIGIBLE,
                blocking_gate_ids=(),
                warning_gate_ids=tuple(result.gate_id for result in warnings),
                reason_codes=tuple(result.reason_code for result in warnings),
                gate_snapshot_hash=snapshot,
            )

        return GateDecision(
            action=action,
            eligibility=EligibilityState.ELIGIBLE,
            blocking_gate_ids=(),
            warning_gate_ids=(),
            reason_codes=tuple(result.reason_code for result in relevant),
            gate_snapshot_hash=snapshot,
        )
