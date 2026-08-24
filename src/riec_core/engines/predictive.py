"""Finite-library predictive-selection contract for synthetic fixtures."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

from ..actions import ActionContext, PredictiveActionRecord
from ..canonical import CanonicalModel, canonical_checksum
from ..gates import GateEngine, GateResult
from ..models import (
    ActionFamily,
    ArtifactOrigin,
    EligibilityState,
    EvidenceAuthority,
    PredictiveAction,
)
from ..protocol import Protocol


@dataclass(frozen=True)
class RiskRecord(CanonicalModel):
    metric_id: str
    metric_version: str
    value: float
    uncertainty: float | None
    unit: str
    panel: str
    denominator: int
    independent_unit: str
    direction: str = "lower_is_better"

    def __post_init__(self) -> None:
        if self.denominator <= 0:
            raise ValueError("risk denominator must be positive")
        if self.direction != "lower_is_better":
            raise ValueError("Phase 3 predictive micro-engine supports lower-is-better risk only")
        if not all((self.metric_id, self.metric_version, self.unit, self.panel, self.independent_unit)):
            raise ValueError("risk identity, unit, panel, and independent unit are required")


@dataclass(frozen=True)
class CandidateEvaluation(CanonicalModel):
    candidate_id: str
    candidate_version: str
    risk: RiskRecord
    worst_unit_metrics: tuple[tuple[str, float], ...]
    stability: float | None
    complexity: float
    deployment_burden: float
    eligible: bool
    authority: EvidenceAuthority
    reason_codes: tuple[str, ...]
    origin: ArtifactOrigin = ArtifactOrigin.RUNTIME_RESULT

    def __post_init__(self) -> None:
        if not self.candidate_id or not self.candidate_version:
            raise ValueError("candidate identity is required")
        if self.complexity < 0 or self.deployment_burden < 0:
            raise ValueError("complexity and burden cannot be negative")

    def worst_unit_value(self) -> float:
        return max((value for _, value in self.worst_unit_metrics), default=self.risk.value)


@dataclass(frozen=True)
class NearOptimalSet(CanonicalModel):
    policy_id: str
    policy_version: str
    reference_candidate_id: str | None
    member_ids: tuple[str, ...]
    threshold_description: str
    interpretation: str = "tolerance_set_not_statistical_equivalence"


class NearOptimalPolicy(ABC):
    policy_id: str
    policy_version: str

    @abstractmethod
    def form(self, candidates: tuple[CandidateEvaluation, ...]) -> NearOptimalSet:
        raise NotImplementedError


@dataclass(frozen=True)
class AbsoluteTolerancePolicy(NearOptimalPolicy, CanonicalModel):
    tolerance: float
    policy_id: str = "absolute_tolerance"
    policy_version: str = "0.1.0"
    origin: ArtifactOrigin = ArtifactOrigin.CONFIGURATION

    def __post_init__(self) -> None:
        if self.tolerance < 0:
            raise ValueError("tolerance cannot be negative")

    def form(self, candidates: tuple[CandidateEvaluation, ...]) -> NearOptimalSet:
        if not candidates:
            return NearOptimalSet(self.policy_id, self.policy_version, None, (), f"absolute<={self.tolerance}")
        best = min(candidates, key=lambda candidate: (candidate.risk.value, candidate.candidate_id))
        members = tuple(
            candidate.candidate_id
            for candidate in sorted(candidates, key=lambda candidate: candidate.candidate_id)
            if candidate.risk.value <= best.risk.value + self.tolerance
        )
        return NearOptimalSet(
            self.policy_id,
            self.policy_version,
            best.candidate_id,
            members,
            f"risk<=best+{self.tolerance}",
        )


@dataclass(frozen=True)
class DecisionOrder(CanonicalModel):
    policy_id: str
    policy_version: str
    fields: tuple[str, ...]
    origin: ArtifactOrigin = ArtifactOrigin.CONFIGURATION

    def __post_init__(self) -> None:
        allowed = {"primary_risk", "worst_unit", "stability", "complexity", "deployment_burden"}
        unknown = set(self.fields) - allowed
        if not self.fields or unknown:
            raise ValueError(f"invalid decision-order fields: {sorted(unknown)}")

    def key(self, candidate: CandidateEvaluation) -> tuple[float | str, ...]:
        values: list[float | str] = []
        for field in self.fields:
            if field == "primary_risk":
                values.append(candidate.risk.value)
            elif field == "worst_unit":
                values.append(candidate.worst_unit_value())
            elif field == "stability":
                values.append(-(candidate.stability if candidate.stability is not None else float("-inf")))
            elif field == "complexity":
                values.append(candidate.complexity)
            elif field == "deployment_burden":
                values.append(candidate.deployment_burden)
        values.append(candidate.candidate_id)
        return tuple(values)


class FallbackPolicy(ABC):
    policy_id: str
    policy_version: str

    @abstractmethod
    def choose(self, candidates: tuple[CandidateEvaluation, ...]) -> CandidateEvaluation | None:
        raise NotImplementedError


@dataclass(frozen=True)
class StableIdFallbackPolicy(FallbackPolicy, CanonicalModel):
    policy_id: str = "stable_id_fallback"
    policy_version: str = "0.1.0"
    origin: ArtifactOrigin = ArtifactOrigin.CONFIGURATION

    def choose(self, candidates: tuple[CandidateEvaluation, ...]) -> CandidateEvaluation | None:
        return min(candidates, key=lambda candidate: candidate.candidate_id) if candidates else None


@dataclass(frozen=True)
class DecisionProvenance(CanonicalModel):
    eligible_candidate_ids: tuple[str, ...]
    near_optimal_member_ids: tuple[str, ...]
    near_optimal_policy_id: str
    decision_order_id: str
    fallback_policy_id: str | None
    preference_trace: tuple[tuple[str, tuple[float | str, ...]], ...]
    origin: ArtifactOrigin = ArtifactOrigin.RUNTIME_RESULT


@dataclass(frozen=True)
class PredictiveDecision(CanonicalModel):
    action_record: PredictiveActionRecord
    near_optimal_set: NearOptimalSet
    provenance: DecisionProvenance


class PredictiveEngine:
    @staticmethod
    def decide(
        protocol: Protocol,
        candidates: Iterable[CandidateEvaluation],
        gates: tuple[GateResult, ...],
        near_optimal_policy: NearOptimalPolicy,
        decision_order: DecisionOrder,
        *,
        fallback_policy: FallbackPolicy | None = None,
        timestamp: datetime | None = None,
    ) -> PredictiveDecision:
        now = timestamp or datetime.now(timezone.utc)
        gate_decision = GateEngine.evaluate(gates, PredictiveAction.SELECT.value)
        eligible = tuple(
            candidate
            for candidate in candidates
            if candidate.eligible and candidate.authority is EvidenceAuthority.FORMAL
        )
        eligible = tuple(sorted(eligible, key=lambda candidate: candidate.candidate_id))

        if gate_decision.eligibility in {EligibilityState.INELIGIBLE, EligibilityState.NOT_EVALUABLE}:
            empty = near_optimal_policy.form(())
            return PredictiveEngine._decision(
                protocol,
                gates,
                PredictiveAction.ABSTAIN,
                None,
                empty,
                eligible,
                decision_order,
                fallback_policy,
                gate_decision.reason_codes + ("PREDICTIVE.GATE_BLOCKED",),
                (),
                now,
            )

        near_set = near_optimal_policy.form(eligible)
        members = tuple(candidate for candidate in eligible if candidate.candidate_id in set(near_set.member_ids))
        if members:
            ordered = tuple(sorted(members, key=decision_order.key))
            selected = ordered[0]
            if gate_decision.eligibility is EligibilityState.CONDITIONALLY_ELIGIBLE:
                conditions = tuple(condition for gate in gates for condition in gate.conditions if gate.state.value == "WARN")
                action = PredictiveAction.SELECT_WITH_CONDITIONS
            else:
                conditions = ()
                action = PredictiveAction.SELECT
            return PredictiveEngine._decision(
                protocol,
                gates,
                action,
                selected,
                near_set,
                eligible,
                decision_order,
                fallback_policy,
                gate_decision.reason_codes + ("PREDICTIVE.PREFERENCE_APPLIED",),
                conditions,
                now,
            )

        fallback = fallback_policy.choose(eligible) if fallback_policy is not None else None
        if fallback is not None:
            return PredictiveEngine._decision(
                protocol,
                gates,
                PredictiveAction.FALLBACK_SELECT,
                fallback,
                near_set,
                eligible,
                decision_order,
                fallback_policy,
                ("PREDICTIVE.PRIMARY_EMPTY", "PREDICTIVE.FALLBACK_APPLIED"),
                ("fallback_policy_used",),
                now,
            )
        return PredictiveEngine._decision(
            protocol,
            gates,
            PredictiveAction.ABSTAIN,
            None,
            near_set,
            eligible,
            decision_order,
            fallback_policy,
            ("PREDICTIVE.NO_ELIGIBLE_ACTION",),
            (),
            now,
        )

    @staticmethod
    def _decision(
        protocol: Protocol,
        gates: tuple[GateResult, ...],
        action: PredictiveAction,
        selected: CandidateEvaluation | None,
        near_set: NearOptimalSet,
        eligible: tuple[CandidateEvaluation, ...],
        decision_order: DecisionOrder,
        fallback_policy: FallbackPolicy | None,
        reason_codes: tuple[str, ...],
        conditions: tuple[str, ...],
        timestamp: datetime,
    ) -> PredictiveDecision:
        family = {
            PredictiveAction.SELECT: ActionFamily.COMMIT,
            PredictiveAction.SELECT_WITH_CONDITIONS: ActionFamily.BOUND,
            PredictiveAction.FALLBACK_SELECT: ActionFamily.BOUND,
            PredictiveAction.ABSTAIN: ActionFamily.NON_DECISION,
            PredictiveAction.DIAGNOSTIC_ONLY: ActionFamily.DIAGNOSTIC_ONLY,
        }[action]
        context = ActionContext(
            action_id=f"predictive:{canonical_checksum((protocol.protocol_id, action.value, selected.candidate_id if selected else None, timestamp))[:20]}",
            protocol_checksum=protocol.checksum(),
            gate_snapshot_hash=canonical_checksum(gates),
            policy_version=decision_order.policy_version,
            reason_codes=reason_codes,
            conditions=conditions,
            selected_object_ids=(selected.candidate_id,) if selected else (),
            claim_scope=None,
            timestamp=timestamp,
        )
        record = PredictiveActionRecord(context, action, family)
        trace = tuple((candidate.candidate_id, decision_order.key(candidate)) for candidate in eligible)
        provenance = DecisionProvenance(
            eligible_candidate_ids=tuple(candidate.candidate_id for candidate in eligible),
            near_optimal_member_ids=near_set.member_ids,
            near_optimal_policy_id=near_set.policy_id,
            decision_order_id=decision_order.policy_id,
            fallback_policy_id=fallback_policy.policy_id if fallback_policy else None,
            preference_trace=trace,
        )
        return PredictiveDecision(record, near_set, provenance)
