"""Small domain-neutral gate evaluators used by synthetic contract tests."""

from __future__ import annotations

from datetime import datetime

from .canonical import canonical_checksum
from .gates import GateResult
from .models import ArtifactOrigin, GateState, Repairability, UncertaintySource
from .protocol import TargetIdentity, UnitDeclaration, UncertaintyProvenance


def target_compatibility_gate(
    left: TargetIdentity, right: TargetIdentity, *, timestamp: datetime
) -> GateResult:
    compatible = (
        left.target_id == right.target_id
        and left.target_kind == right.target_kind
        and left.unit == right.unit
        and left.scale == right.scale
        and left.support.checksum() == right.support.checksum()
        and left.feature_context_id == right.feature_context_id
    )
    return GateResult(
        gate_id="G1",
        gate_version="0.1.0",
        state=GateState.PASS if compatible else GateState.FAIL,
        reason_code="CORE.G1.TARGET_COMPATIBLE" if compatible else "CORE.G1.TARGET_MISMATCH",
        evidence_refs=(left.checksum(), right.checksum()),
        affected_actions=("*",),
        repairability=Repairability.INTRINSIC_INCOMPATIBILITY,
        timestamp=timestamp,
        config_hash=canonical_checksum({"rule": "target_compatibility", "version": "0.1.0"}),
        origin=ArtifactOrigin.RUNTIME_RESULT,
    )


def deployment_defined_gate(unit: UnitDeclaration, *, timestamp: datetime) -> GateResult:
    defined = not unit.unresolved_identity and unit.unit_type != "UNDEFINED" and bool(unit.key_fields)
    return GateResult(
        gate_id="G3",
        gate_version="0.1.0",
        state=GateState.PASS if defined else GateState.NOT_EVALUABLE,
        reason_code="CORE.G3.DEPLOYMENT_DEFINED" if defined else "CORE.G3.DEPLOYMENT_UNDEFINED",
        evidence_refs=(unit.checksum(),),
        affected_actions=("*",),
        repairability=Repairability.EVIDENCE_ACQUIRABLE,
        timestamp=timestamp,
        config_hash=canonical_checksum({"rule": "deployment_defined", "version": "0.1.0"}),
        origin=ArtifactOrigin.RUNTIME_RESULT,
    )


def leakage_sentinel(
    train_unit_keys: tuple[str, ...], test_unit_keys: tuple[str, ...], *, timestamp: datetime
) -> GateResult:
    overlap = tuple(sorted(set(train_unit_keys) & set(test_unit_keys)))
    return GateResult(
        gate_id="G3",
        gate_version="0.1.0",
        state=GateState.FAIL if overlap else GateState.PASS,
        reason_code="CORE.G3.UNIT_LEAKAGE" if overlap else "CORE.G3.NO_UNIT_LEAKAGE",
        evidence_refs=overlap or (canonical_checksum({"train": train_unit_keys, "test": test_unit_keys}),),
        affected_actions=("*",),
        repairability=Repairability.DATA_CORRECTABLE,
        timestamp=timestamp,
        config_hash=canonical_checksum({"rule": "unit_overlap", "version": "0.1.0"}),
        origin=ArtifactOrigin.RUNTIME_RESULT,
    )


def support_gate(count: int, minimum: int, *, timestamp: datetime) -> GateResult:
    if minimum <= 0:
        raise ValueError("support minimum must be positive")
    return GateResult(
        gate_id="G4",
        gate_version="0.1.0",
        state=GateState.PASS if count >= minimum else GateState.FAIL,
        reason_code="CORE.G4.SUPPORT_SUFFICIENT" if count >= minimum else "CORE.G4.SUPPORT_INSUFFICIENT",
        evidence_refs=(f"count:{count}", f"minimum:{minimum}"),
        affected_actions=("*",),
        repairability=Repairability.EVIDENCE_ACQUIRABLE,
        timestamp=timestamp,
        config_hash=canonical_checksum({"rule": "minimum_support", "minimum": minimum}),
        origin=ArtifactOrigin.RUNTIME_RESULT,
    )


def uncertainty_route_gate(
    uncertainty: UncertaintyProvenance, *, requires_variance: bool, timestamp: datetime
) -> GateResult:
    unavailable = requires_variance and uncertainty.source_class is UncertaintySource.UNAVAILABLE
    return GateResult(
        gate_id="G5",
        gate_version="0.1.0",
        state=GateState.NOT_EVALUABLE if unavailable else GateState.PASS,
        reason_code="CORE.G5.VARIANCE_UNAVAILABLE" if unavailable else "CORE.G5.UNCERTAINTY_ELIGIBLE",
        evidence_refs=(uncertainty.checksum(),),
        affected_actions=("RESOLVE",),
        repairability=Repairability.EVIDENCE_ACQUIRABLE,
        timestamp=timestamp,
        config_hash=canonical_checksum({"rule": "uncertainty_route", "requires_variance": requires_variance}),
        origin=ArtifactOrigin.RUNTIME_RESULT,
    )
