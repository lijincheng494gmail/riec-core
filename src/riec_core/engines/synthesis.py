"""Bounded evidence-synthesis contract for synthetic fixtures."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Iterable

from ..actions import ActionContext, SynthesisActionRecord
from ..canonical import CanonicalModel, canonical_checksum
from ..gates import GateEngine, GateResult
from ..models import ActionFamily, ArtifactOrigin, EligibilityState, SynthesisAction, UncertaintySource
from ..protocol import Protocol


class WeightingRoute(str, Enum):
    NONE = "none"
    INVERSE_VARIANCE = "inverse_variance"


class InsufficientSupportPolicy(str, Enum):
    ABSTAIN = "ABSTAIN"
    DOWNGRADE = "DOWNGRADE"


@dataclass(frozen=True)
class ClaimWorld(CanonicalModel):
    claim_world_id: str
    claim_world_version: str
    target_id: str
    estimand_id: str
    support_id: str
    translation_id: str
    origin: ArtifactOrigin = ArtifactOrigin.CONFIGURATION

    def __post_init__(self) -> None:
        if not all((self.claim_world_id, self.claim_world_version, self.target_id, self.estimand_id, self.support_id, self.translation_id)):
            raise ValueError("complete claim-world identity is required")


@dataclass(frozen=True)
class EvidenceNode(CanonicalModel):
    node_id: str
    protocol_id: str
    claim_world: ClaimWorld
    eligible: bool
    uncertainty_source: UncertaintySource
    provenance_refs: tuple[str, ...]
    origin: ArtifactOrigin = ArtifactOrigin.RUNTIME_RESULT

    def __post_init__(self) -> None:
        if not self.node_id or not self.protocol_id or not self.provenance_refs:
            raise ValueError("evidence node identity and provenance are required")


@dataclass(frozen=True)
class ClaimPartition(CanonicalModel):
    partition_id: str
    claim_world_checksum: str
    node_ids: tuple[str, ...]


@dataclass(frozen=True)
class SynthesisDecision(CanonicalModel):
    action_record: SynthesisActionRecord
    partitions: tuple[ClaimPartition, ...]
    weighting_route: WeightingRoute
    eligible_node_ids: tuple[str, ...]


class SynthesisEngine:
    @staticmethod
    def partition(nodes: Iterable[EvidenceNode]) -> tuple[ClaimPartition, ...]:
        grouped: dict[str, list[str]] = {}
        for node in nodes:
            if not node.eligible:
                continue
            key = node.claim_world.checksum()
            grouped.setdefault(key, []).append(node.node_id)
        return tuple(
            ClaimPartition(
                partition_id=f"partition:{checksum[:16]}",
                claim_world_checksum=checksum,
                node_ids=tuple(sorted(grouped[checksum])),
            )
            for checksum in sorted(grouped)
        )

    @staticmethod
    def decide(
        protocol: Protocol,
        nodes: Iterable[EvidenceNode],
        gates: tuple[GateResult, ...],
        *,
        weighting_route: WeightingRoute,
        minimum_support: int,
        insufficient_support_policy: InsufficientSupportPolicy,
        timestamp: datetime | None = None,
    ) -> SynthesisDecision:
        if minimum_support <= 0:
            raise ValueError("minimum_support must be positive")
        now = timestamp or datetime.now(timezone.utc)
        eligible_nodes = tuple(sorted((node for node in nodes if node.eligible), key=lambda node: node.node_id))
        partitions = SynthesisEngine.partition(eligible_nodes)
        gate_decision = GateEngine.evaluate(gates, SynthesisAction.RESOLVE.value)

        if gate_decision.eligibility in {EligibilityState.INELIGIBLE, EligibilityState.NOT_EVALUABLE}:
            return SynthesisEngine._decision(
                protocol, gates, SynthesisAction.ABSTAIN, (), partitions, eligible_nodes, weighting_route,
                gate_decision.reason_codes + ("SYNTHESIS.GATE_BLOCKED",), None, now,
            )

        if gate_decision.eligibility is EligibilityState.CONDITIONALLY_ELIGIBLE:
            return SynthesisEngine._bounded_or_abstain(
                protocol, gates, partitions, eligible_nodes, weighting_route,
                "SYNTHESIS.WARN_REQUIRES_BOUND", "conditional_claim_only", now,
            )

        if not eligible_nodes:
            return SynthesisEngine._decision(
                protocol, gates, SynthesisAction.ABSTAIN, (), partitions, eligible_nodes, weighting_route,
                ("SYNTHESIS.NO_ELIGIBLE_EVIDENCE",), None, now,
            )

        if len(partitions) > 1:
            return SynthesisEngine._decision(
                protocol, gates, SynthesisAction.STRATIFY,
                tuple(partition.partition_id for partition in partitions), partitions, eligible_nodes, weighting_route,
                ("SYNTHESIS.MULTIPLE_CLAIM_WORLDS",), "partition_specific_claims", now,
            )

        if len(eligible_nodes) < minimum_support:
            if insufficient_support_policy is InsufficientSupportPolicy.DOWNGRADE:
                return SynthesisEngine._bounded_or_abstain(
                    protocol, gates, partitions, eligible_nodes, weighting_route,
                    "SYNTHESIS.SUPPORT_INSUFFICIENT", "audit_only", now,
                )
            return SynthesisEngine._decision(
                protocol, gates, SynthesisAction.ABSTAIN, (), partitions, eligible_nodes, weighting_route,
                ("SYNTHESIS.SUPPORT_INSUFFICIENT",), None, now,
            )

        if weighting_route is WeightingRoute.INVERSE_VARIANCE and any(
            node.uncertainty_source is UncertaintySource.UNAVAILABLE for node in eligible_nodes
        ):
            return SynthesisEngine._bounded_or_abstain(
                protocol, gates, partitions, eligible_nodes, weighting_route,
                "SYNTHESIS.VARIANCE_UNAVAILABLE", "unweighted_audit_only", now,
            )

        return SynthesisEngine._decision(
            protocol, gates, SynthesisAction.RESOLVE,
            tuple(node.node_id for node in eligible_nodes), partitions, eligible_nodes, weighting_route,
            ("SYNTHESIS.SAME_PARTITION_ELIGIBLE",), "registered_claim_world", now,
        )

    @staticmethod
    def _bounded_or_abstain(
        protocol: Protocol,
        gates: tuple[GateResult, ...],
        partitions: tuple[ClaimPartition, ...],
        nodes: tuple[EvidenceNode, ...],
        weighting_route: WeightingRoute,
        reason: str,
        claim_scope: str,
        timestamp: datetime,
    ) -> SynthesisDecision:
        if SynthesisAction.DOWNGRADE.value in protocol.translation_rule.allowed_actions:
            return SynthesisEngine._decision(
                protocol, gates, SynthesisAction.DOWNGRADE,
                tuple(node.node_id for node in nodes), partitions, nodes, weighting_route,
                (reason,), claim_scope, timestamp,
            )
        return SynthesisEngine._decision(
            protocol, gates, SynthesisAction.ABSTAIN, (), partitions, nodes, weighting_route,
            (reason, "SYNTHESIS.DOWNGRADE_NOT_DECLARED"), None, timestamp,
        )

    @staticmethod
    def _decision(
        protocol: Protocol,
        gates: tuple[GateResult, ...],
        action: SynthesisAction,
        selected_ids: tuple[str, ...],
        partitions: tuple[ClaimPartition, ...],
        nodes: tuple[EvidenceNode, ...],
        weighting_route: WeightingRoute,
        reasons: tuple[str, ...],
        claim_scope: str | None,
        timestamp: datetime,
    ) -> SynthesisDecision:
        family = {
            SynthesisAction.RESOLVE: ActionFamily.COMMIT,
            SynthesisAction.STRATIFY: ActionFamily.PARTITION,
            SynthesisAction.DOWNGRADE: ActionFamily.BOUND,
            SynthesisAction.ABSTAIN: ActionFamily.NON_DECISION,
            SynthesisAction.DIAGNOSTIC_ONLY: ActionFamily.DIAGNOSTIC_ONLY,
        }[action]
        context = ActionContext(
            action_id=f"synthesis:{canonical_checksum((protocol.protocol_id, action.value, selected_ids, timestamp))[:20]}",
            protocol_checksum=protocol.checksum(),
            gate_snapshot_hash=canonical_checksum(gates),
            policy_version="0.1.0",
            reason_codes=reasons,
            conditions=(),
            selected_object_ids=selected_ids,
            claim_scope=claim_scope,
            timestamp=timestamp,
        )
        record = SynthesisActionRecord(context, action, family)
        return SynthesisDecision(record, partitions, weighting_route, tuple(node.node_id for node in nodes))
