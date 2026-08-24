"""Domain adapter contract and mapping-only scaffold implementation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any

from riec_core.actions import ActionRecord
from riec_core.audit import AuditBundleManifest
from riec_core.canonical import CanonicalModel
from riec_core.gates import GateResult
from riec_core.models import ArtifactOrigin, ScientificStatus, TaskFamily
from riec_core.protocol import Protocol, TargetIdentity, UnitDeclaration, UncertaintyProvenance
from riec_core.quarantine import QuarantineRecord


class AdapterLifecycle(str, Enum):
    MIGRATION_SCAFFOLD = "MIGRATION_SCAFFOLD"
    NOT_STARTED = "NOT_STARTED"
    LOCKBOX_NOT_OPENED = "LOCKBOX_NOT_OPENED"
    DEVELOPMENT_READY = "DEVELOPMENT_READY"
    DEVELOPMENT_VALIDATED = "DEVELOPMENT_VALIDATED"


class ScientificExecutionForbidden(RuntimeError):
    pass


class LockboxClosedError(ScientificExecutionForbidden):
    pass


@dataclass(frozen=True)
class LifecycleEvidence(CanonicalModel):
    frozen_artifact_refs: tuple[str, ...]
    smoke_audit_reference: str | None
    formal_manifest_reference: str | None
    validation_audit_reference: str | None


_READY_EVIDENCE = {"target", "unit", "protocol", "split", "constraint", "adapter"}


def validate_lifecycle_transition(
    current: AdapterLifecycle,
    requested: AdapterLifecycle,
    evidence: LifecycleEvidence,
) -> None:
    """Implement the accepted shared lifecycle amendment without running science."""

    if current is AdapterLifecycle.MIGRATION_SCAFFOLD and requested in {
        AdapterLifecycle.DEVELOPMENT_READY,
        AdapterLifecycle.DEVELOPMENT_VALIDATED,
    }:
        raise ValueError("a migration adapter cannot silently become a development adapter")
    if requested is AdapterLifecycle.DEVELOPMENT_READY:
        if not _READY_EVIDENCE.issubset(set(evidence.frozen_artifact_refs)) or not evidence.smoke_audit_reference:
            raise ValueError("DEVELOPMENT_READY requires frozen inputs and a smoke audit")
    if requested is AdapterLifecycle.DEVELOPMENT_VALIDATED:
        if not _READY_EVIDENCE.issubset(set(evidence.frozen_artifact_refs)):
            raise ValueError("DEVELOPMENT_VALIDATED requires frozen development inputs")
        if not all((evidence.smoke_audit_reference, evidence.formal_manifest_reference, evidence.validation_audit_reference)):
            raise ValueError("DEVELOPMENT_VALIDATED requires formal and validation audit references")



@dataclass(frozen=True)
class AdapterDescriptor(CanonicalModel):
    adapter_id: str
    adapter_version: str
    task_family: TaskFamily
    lifecycle: AdapterLifecycle
    origin: ArtifactOrigin
    discrepancy_ids: tuple[str, ...]
    limitations: tuple[str, ...]


@dataclass(frozen=True)
class SplitManifest(CanonicalModel):
    split_id: str
    split_version: str
    status: ScientificStatus
    membership_refs: tuple[str, ...]
    origin: ArtifactOrigin


@dataclass(frozen=True)
class ActionTranslation(CanonicalModel):
    action_id: str
    translation_policy_id: str
    bounded_text: str
    claim_scope: str | None
    origin: ArtifactOrigin


class DomainAdapter(ABC):
    @property
    @abstractmethod
    def descriptor(self) -> AdapterDescriptor:
        raise NotImplementedError

    @abstractmethod
    def describe_target(self) -> TargetIdentity:
        raise NotImplementedError

    @abstractmethod
    def define_units(self) -> tuple[UnitDeclaration, UnitDeclaration]:
        raise NotImplementedError

    @abstractmethod
    def register_protocols(self) -> tuple[Protocol, ...]:
        raise NotImplementedError

    @abstractmethod
    def build_splits(self) -> SplitManifest:
        raise NotImplementedError

    @abstractmethod
    def evaluate_domain_constraints(self) -> tuple[GateResult, ...]:
        raise NotImplementedError

    @abstractmethod
    def map_uncertainty(self) -> tuple[UncertaintyProvenance, ...]:
        raise NotImplementedError

    @abstractmethod
    def run_candidates(self) -> tuple[Any, ...]:
        raise NotImplementedError

    @abstractmethod
    def build_evidence_graph(self) -> tuple[Any, ...]:
        raise NotImplementedError

    @abstractmethod
    def translate_output(self, action: ActionRecord) -> ActionTranslation:
        raise NotImplementedError

    @abstractmethod
    def export_audit_bundle(self) -> AuditBundleManifest | None:
        raise NotImplementedError

    @abstractmethod
    def quarantine_records(self) -> tuple[QuarantineRecord, ...]:
        raise NotImplementedError


class MappingScaffoldAdapter(DomainAdapter):
    """Implements mapping surfaces while making scientific execution impossible."""

    def __init__(
        self,
        descriptor: AdapterDescriptor,
        target: TargetIdentity,
        units: tuple[UnitDeclaration, UnitDeclaration],
        quarantines: tuple[QuarantineRecord, ...],
    ) -> None:
        self._descriptor = descriptor
        self._target = target
        self._units = units
        self._quarantines = quarantines

    @property
    def descriptor(self) -> AdapterDescriptor:
        return self._descriptor

    def describe_target(self) -> TargetIdentity:
        return self._target

    def define_units(self) -> tuple[UnitDeclaration, UnitDeclaration]:
        return self._units

    def register_protocols(self) -> tuple[Protocol, ...]:
        return ()

    def build_splits(self) -> SplitManifest:
        return SplitManifest(
            split_id=f"{self.descriptor.adapter_id}:not_materialized",
            split_version="0.1.0",
            status=ScientificStatus.NOT_STARTED,
            membership_refs=(),
            origin=ArtifactOrigin.NEW_ARCHITECTURE_PROPOSAL,
        )

    def evaluate_domain_constraints(self) -> tuple[GateResult, ...]:
        return ()

    def map_uncertainty(self) -> tuple[UncertaintyProvenance, ...]:
        return ()

    def run_candidates(self) -> tuple[Any, ...]:
        raise ScientificExecutionForbidden("Phase 3 adapters cannot run scientific candidates")

    def build_evidence_graph(self) -> tuple[Any, ...]:
        raise ScientificExecutionForbidden("Phase 3 adapters cannot build historical evidence graphs")

    def translate_output(self, action: ActionRecord) -> ActionTranslation:
        return ActionTranslation(
            action_id=action.context.action_id,
            translation_policy_id="phase3.mapping_only",
            bounded_text="Mapping scaffold only; no scientific or operational claim.",
            claim_scope=action.context.claim_scope,
            origin=ArtifactOrigin.NEW_ARCHITECTURE_PROPOSAL,
        )

    def export_audit_bundle(self) -> AuditBundleManifest | None:
        return None

    def quarantine_records(self) -> tuple[QuarantineRecord, ...]:
        return self._quarantines
