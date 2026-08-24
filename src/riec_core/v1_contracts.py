"""Versioned v1 RC governance records; no domain calculation is implemented here."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from typing import Any, Mapping

from .canonical import CanonicalModel
from .models import GateState


_SHA256 = re.compile(r"^[a-f0-9]{64}$")
_VERSION = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+-rc\.[1-9][0-9]*$")


class MetricApplicability(str, Enum):
    EVALUABLE = "EVALUABLE"
    NOT_EVALUABLE = "NOT_EVALUABLE"
    SECONDARY_ONLY = "SECONDARY_ONLY"
    DIAGNOSTIC_ONLY = "DIAGNOSTIC_ONLY"
    NOT_RECORDED = "NOT_RECORDED"


class MetricValidity(str, Enum):
    VALID = "VALID"
    INVALID = "INVALID"
    NOT_EVALUABLE = "NOT_EVALUABLE"
    NOT_RECORDED = "NOT_RECORDED"


class AggregationEligibility(str, Enum):
    INCLUDE = "INCLUDE"
    EXCLUDE_UNDEFINED_ONLY = "EXCLUDE_UNDEFINED_ONLY"
    EXCLUDE_INVALID = "EXCLUDE_INVALID"
    NOT_RECORDED = "NOT_RECORDED"


class OptimizerStatus(str, Enum):
    CONVERGED = "CONVERGED"
    WARNING = "WARNING"
    FAILED = "FAILED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NOT_REPORTED = "NOT_REPORTED"


class ActionQualification(str, Enum):
    NONE = "NONE"
    WITH_CONDITIONS = "WITH_CONDITIONS"


class AdapterLifecycleV1(str, Enum):
    MIGRATION_SCAFFOLD = "MIGRATION_SCAFFOLD"
    NOT_STARTED = "NOT_STARTED"
    LOCKBOX_NOT_OPENED = "LOCKBOX_NOT_OPENED"
    DEVELOPMENT_READY = "DEVELOPMENT_READY"
    DEVELOPMENT_VALIDATED = "DEVELOPMENT_VALIDATED"


class ThresholdOwner(str, Enum):
    CORE_STRUCTURAL = "CORE_STRUCTURAL"
    ENGINE = "ENGINE"
    ADAPTER = "ADAPTER"


class ReleaseStatus(str, Enum):
    RELEASE_CANDIDATE_NOT_FROZEN = "RELEASE_CANDIDATE_NOT_FROZEN"


@dataclass(frozen=True)
class MetricContractV1(CanonicalModel):
    metric_or_loss_id: str
    metric_exists: bool | None
    applicability: MetricApplicability
    validity: MetricValidity
    aggregation_eligibility: AggregationEligibility
    aggregation_rule: str
    undefined_handling: str
    risk_functional: str | None = None

    def __post_init__(self) -> None:
        if not self.metric_or_loss_id or not self.aggregation_rule or not self.undefined_handling:
            raise ValueError("metric identity, aggregation rule, and undefined handling are required")
        if self.metric_exists is False and self.applicability not in {
            MetricApplicability.NOT_EVALUABLE,
            MetricApplicability.NOT_RECORDED,
        }:
            raise ValueError("an absent metric cannot be applicable")
        if self.applicability is MetricApplicability.NOT_EVALUABLE and self.validity is MetricValidity.VALID:
            raise ValueError("an inapplicable metric cannot be marked valid")
        if self.applicability is MetricApplicability.NOT_EVALUABLE and self.aggregation_eligibility is AggregationEligibility.INCLUDE:
            raise ValueError("an inapplicable metric cannot be aggregated")


@dataclass(frozen=True)
class CandidateValidityV1(CanonicalModel):
    fit_status: str
    finite_output: bool | None
    optimizer_status: OptimizerStatus
    warning_codes: tuple[str, ...]
    adapter_validity_state: GateState
    adapter_policy_id: str
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.fit_status or not self.adapter_policy_id:
            raise ValueError("fit status and adapter policy are required")
        if self.optimizer_status is OptimizerStatus.NOT_REPORTED and self.adapter_validity_state is GateState.PASS:
            raise ValueError("missing optimizer provenance cannot be fabricated as PASS")
        if self.optimizer_status is OptimizerStatus.FAILED and self.adapter_validity_state is GateState.PASS:
            raise ValueError("an explicit optimizer failure cannot be accepted as PASS")


@dataclass(frozen=True)
class ConstraintResultV1(CanonicalModel):
    primary_event: str | None
    conditions: tuple[str, ...]
    primary_event_source_hash: str
    legacy_event_preserved: bool

    def __post_init__(self) -> None:
        if not _SHA256.fullmatch(self.primary_event_source_hash):
            raise ValueError("primary event source hash must be SHA-256")
        if len(self.conditions) != len(set(self.conditions)):
            raise ValueError("constraint conditions must be unique")
        if not self.legacy_event_preserved:
            raise ValueError("the canonical primary event cannot be rewritten")


_BASE_ACTIONS = {
    "SELECT",
    "RESOLVE",
    "STRATIFY",
    "DOWNGRADE",
    "ABSTAIN",
    "FALLBACK_SELECT",
    "DIAGNOSTIC_ONLY",
}


@dataclass(frozen=True)
class ActionEnvelopeV1(CanonicalModel):
    base_action: str
    qualification: ActionQualification
    conditions: tuple[str, ...]
    legacy_serialized_action: str | None

    def __post_init__(self) -> None:
        if self.base_action not in _BASE_ACTIONS:
            raise ValueError(f"unsupported base action: {self.base_action}")
        if self.qualification is ActionQualification.WITH_CONDITIONS:
            if self.base_action != "SELECT" or not self.conditions:
                raise ValueError("WITH_CONDITIONS requires SELECT and nonempty conditions")
        if self.qualification is ActionQualification.NONE and self.conditions:
            raise ValueError("unqualified actions cannot carry hidden conditions")

    @classmethod
    def from_legacy(cls, action: str, *, conditions: tuple[str, ...] = ()) -> "ActionEnvelopeV1":
        if action == "SELECT_WITH_CONDITIONS":
            return cls("SELECT", ActionQualification.WITH_CONDITIONS, conditions, action)
        return cls(action, ActionQualification.NONE, (), action)

    def to_legacy(self) -> str:
        if self.legacy_serialized_action:
            return self.legacy_serialized_action
        if self.base_action == "SELECT" and self.qualification is ActionQualification.WITH_CONDITIONS:
            return "SELECT_WITH_CONDITIONS"
        return self.base_action


@dataclass(frozen=True)
class ThresholdRecordV1(CanonicalModel):
    threshold_id: str
    owner: ThresholdOwner
    scope: str
    value: Any
    provenance: str
    sensitivity_status: str
    change_authority: str
    universal_across_domains: bool = False

    def __post_init__(self) -> None:
        if not all((self.threshold_id, self.scope, self.provenance, self.sensitivity_status, self.change_authority)):
            raise ValueError("threshold identity, scope, provenance, sensitivity, and authority are required")
        if self.universal_across_domains:
            raise ValueError("the v1 RC does not contain universal numeric thresholds")


@dataclass(frozen=True)
class GateSemanticBoundaryV1(CanonicalModel):
    support_gate_id: str
    admissibility_gate_id: str
    relationship: str
    merged: bool

    def __post_init__(self) -> None:
        if self.support_gate_id != "G4" or self.admissibility_gate_id != "G6":
            raise ValueError("the v1 RC boundary is defined only for G4 and G6")
        if self.relationship != "DISTINCT_WITH_CONDITIONAL_OVERLAP" or self.merged:
            raise ValueError("G4 and G6 must remain distinct with conditional overlap")


_FORBIDDEN_CLAIMS = {
    "UNIVERSAL_GATE_NECESSITY",
    "UNIVERSAL_THRESHOLD_VALIDITY",
    "UNIVERSAL_CROSS_DOMAIN_TRANSPORT",
    "PROSPECTIVE_EXTERNAL_VALIDITY",
    "COMPLETE_MATCHED_ACTIVATION_COVERAGE",
    "COMPONENT_OR_ROUTE_CAUSAL_BENEFIT",
    "LOCKBOX_TRANSFER_VALIDATION",
}


@dataclass(frozen=True)
class AuditEnvelopeV1(CanonicalModel):
    source_hashes: tuple[tuple[str, str], ...]
    gate_snapshot: str
    negative_results_retained: bool
    amendment_ids: tuple[str, ...]
    post_waiver_boundary_hash: str
    claims: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.source_hashes or not _SHA256.fullmatch(self.gate_snapshot):
            raise ValueError("source hashes and gate snapshot are required")
        for source_id, digest in self.source_hashes:
            if not source_id or not _SHA256.fullmatch(digest):
                raise ValueError("every source must have a valid SHA-256")
        if not self.negative_results_retained:
            raise ValueError("negative results must be retained")
        if not _SHA256.fullmatch(self.post_waiver_boundary_hash):
            raise ValueError("post-waiver boundary hash must be SHA-256")
        forbidden = _FORBIDDEN_CLAIMS.intersection(self.claims)
        if forbidden:
            raise ValueError(f"post-waiver claim boundary violation: {sorted(forbidden)}")


@dataclass(frozen=True)
class ReleaseIdentityV1(CanonicalModel):
    core_version: str
    status: ReleaseStatus
    source_v0_9_hash: str
    changeset_freeze_hash: str

    def __post_init__(self) -> None:
        if not _VERSION.fullmatch(self.core_version):
            raise ValueError("RC version must use MAJOR.MINOR.PATCH-rc.N")
        if not _SHA256.fullmatch(self.source_v0_9_hash) or not _SHA256.fullmatch(self.changeset_freeze_hash):
            raise ValueError("release identity hashes must be SHA-256")


def validate_v1_document(document: Mapping[str, Any]) -> None:
    """Small dependency-free invariant check used in addition to JSON Schema."""

    required = {"identity", "protocol", "gate_results", "action", "audit"}
    missing = required - set(document)
    if missing:
        raise ValueError(f"v1 document missing fields: {sorted(missing)}")
    identity = document["identity"]
    if identity.get("status") != ReleaseStatus.RELEASE_CANDIDATE_NOT_FROZEN.value:
        raise ValueError("only an unfrozen release candidate is valid in this package")
    audit = document["audit"]
    if audit.get("negative_results_retained") is not True:
        raise ValueError("negative results must remain retained")

