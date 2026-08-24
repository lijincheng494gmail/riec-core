"""Typed RIEC-Core protocol envelope."""

from __future__ import annotations

from dataclasses import dataclass, fields
import re
from typing import Any, Mapping

from .canonical import CanonicalModel
from .models import (
    ArtifactOrigin,
    EvidenceAuthority,
    RegistrationStatus,
    ScientificStatus,
    TaskFamily,
    UncertaintySource,
    WeightingMode,
)


_VERSION = re.compile(r"^[0-9]+\.[0-9]+(?:\.[0-9]+)?(?:-[A-Za-z0-9.-]+)?$")
_SHA256 = re.compile(r"^[a-f0-9]{64}$")


def _nonempty(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


def _version(value: str, field_name: str = "version") -> None:
    if not _VERSION.fullmatch(value):
        raise ValueError(f"{field_name} must be an explicit version")


def _strict_keys(cls: type, payload: Mapping[str, Any]) -> None:
    expected = {field.name for field in fields(cls)}
    supplied = set(payload)
    if supplied != expected:
        missing = sorted(expected - supplied)
        extra = sorted(supplied - expected)
        raise ValueError(f"{cls.__name__} keys mismatch; missing={missing}; extra={extra}")


@dataclass(frozen=True)
class SupportDefinition(CanonicalModel):
    version: str
    population: str
    inclusion_summary: str
    exclusion_summary: str

    def __post_init__(self) -> None:
        _version(self.version)
        _nonempty(self.population, "population")


@dataclass(frozen=True)
class EvidenceSubset(CanonicalModel):
    version: str
    source_ids: tuple[str, ...]
    inclusion_rule_ids: tuple[str, ...]
    exclusion_rule_ids: tuple[str, ...]
    diagnostic_only_source_ids: tuple[str, ...]
    scientific_status: ScientificStatus

    def __post_init__(self) -> None:
        _version(self.version)
        if not self.source_ids:
            raise ValueError("evidence subset requires at least one source ID")


@dataclass(frozen=True)
class TargetIdentity(CanonicalModel):
    version: str
    target_id: str
    target_kind: str
    unit: str | None
    scale: str
    support: SupportDefinition
    horizon: str | None
    feature_context_id: str | None
    allowed_claims: tuple[str, ...]
    prohibited_claims: tuple[str, ...]
    scientific_status: ScientificStatus

    def __post_init__(self) -> None:
        _version(self.version)
        _nonempty(self.target_id, "target_id")
        _nonempty(self.target_kind, "target_kind")
        _nonempty(self.scale, "scale")


@dataclass(frozen=True)
class UnitDeclaration(CanonicalModel):
    version: str
    unit_type: str
    key_fields: tuple[str, ...]
    nesting_fields: tuple[str, ...]
    relation_model: str
    unresolved_identity: bool
    unresolved_reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        _version(self.version)
        _nonempty(self.unit_type, "unit_type")
        _nonempty(self.relation_model, "relation_model")
        if self.unresolved_identity and not self.unresolved_reason_codes:
            raise ValueError("unresolved unit identity requires a reason code")


@dataclass(frozen=True)
class PreprocessingValidation(CanonicalModel):
    version: str
    preprocessing_contract: str
    learned_steps: tuple[str, ...]
    fit_scope: str
    split_contract: str
    tuning_contract: str
    leakage_controls: tuple[str, ...]
    authority: EvidenceAuthority
    split_fingerprint: str | None

    def __post_init__(self) -> None:
        _version(self.version)
        _nonempty(self.preprocessing_contract, "preprocessing_contract")
        _nonempty(self.split_contract, "split_contract")
        if self.split_fingerprint is not None and not _SHA256.fullmatch(self.split_fingerprint):
            raise ValueError("split_fingerprint must be SHA-256")


@dataclass(frozen=True)
class MethodSpec(CanonicalModel):
    version: str
    analysis_type: str
    library_id: str
    method_ids: tuple[str, ...]
    baseline_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _version(self.version)
        _nonempty(self.analysis_type, "analysis_type")
        _nonempty(self.library_id, "library_id")
        if not self.method_ids:
            raise ValueError("method library cannot be empty")


@dataclass(frozen=True)
class UncertaintyProvenance(CanonicalModel):
    version: str
    uncertainty_type: str
    source_class: UncertaintySource
    derivation_id: str | None
    assumptions: tuple[str, ...]
    missingness_policy: str
    eligible_uses: tuple[str, ...]
    scientific_status: ScientificStatus

    def __post_init__(self) -> None:
        _version(self.version)
        _nonempty(self.uncertainty_type, "uncertainty_type")
        _nonempty(self.missingness_policy, "missingness_policy")


@dataclass(frozen=True)
class DecisionWeighting(CanonicalModel):
    version: str
    mode: WeightingMode
    policy_id: str
    parameter_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        _version(self.version)
        _nonempty(self.policy_id, "policy_id")


@dataclass(frozen=True)
class DomainConstraints(CanonicalModel):
    version: str
    rule_registry_id: str
    rule_ids: tuple[str, ...]
    calibration_domain_id: str | None
    expert_review_required: bool

    def __post_init__(self) -> None:
        _version(self.version)
        _nonempty(self.rule_registry_id, "rule_registry_id")


@dataclass(frozen=True)
class TranslationRule(CanonicalModel):
    version: str
    action_vocabulary_version: str
    policy_id: str
    reason_code_namespace: str
    allowed_actions: tuple[str, ...]

    def __post_init__(self) -> None:
        _version(self.version)
        _version(self.action_vocabulary_version, "action_vocabulary_version")
        _nonempty(self.policy_id, "translation policy_id")
        if not self.allowed_actions:
            raise ValueError("translation must declare allowed actions")


@dataclass(frozen=True)
class SourceProvenance(CanonicalModel):
    version: str
    source_manifest_id: str
    source_hashes: tuple[tuple[str, str], ...]
    policy_id: str
    freeze_id: str | None
    amendment_id: str | None
    lineage: tuple[str, ...]
    origin: ArtifactOrigin

    def __post_init__(self) -> None:
        _version(self.version)
        _nonempty(self.source_manifest_id, "source_manifest_id")
        for source_id, checksum in self.source_hashes:
            _nonempty(source_id, "source_id")
            if not _SHA256.fullmatch(checksum):
                raise ValueError(f"invalid SHA-256 for source {source_id}")


@dataclass(frozen=True)
class Protocol(CanonicalModel):
    protocol_id: str
    protocol_version: str
    schema_version: str
    task_family: TaskFamily
    evidence_subset: EvidenceSubset
    target: TargetIdentity
    independent_unit: UnitDeclaration
    deployment_unit: UnitDeclaration
    preprocessing_validation: PreprocessingValidation
    method: MethodSpec
    uncertainty_provenance: UncertaintyProvenance
    decision_weighting: DecisionWeighting
    domain_constraints: DomainConstraints
    translation_rule: TranslationRule
    source_provenance: SourceProvenance
    registration_status: RegistrationStatus
    origin: ArtifactOrigin

    def __post_init__(self) -> None:
        _nonempty(self.protocol_id, "protocol_id")
        _version(self.protocol_version, "protocol_version")
        _version(self.schema_version, "schema_version")
        if self.task_family is TaskFamily.PREDICTIVE_SELECTION and self.decision_weighting.mode is WeightingMode.EVIDENCE_WEIGHTING:
            raise ValueError("predictive protocol cannot use synthesis evidence weighting")
        if self.task_family is TaskFamily.EVIDENCE_SYNTHESIS and self.decision_weighting.mode is WeightingMode.DECISION_COSTS:
            raise ValueError("synthesis protocol cannot use predictive decision costs")
        if self.registration_status is RegistrationStatus.REGISTERED and self.source_provenance.freeze_id is None:
            raise ValueError("registered protocol requires a freeze reference, including a draft freeze ID")

    def semantic_checksum(self) -> str:
        """Checksum every scientific field; registration status is intentionally included."""

        return self.checksum()

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "Protocol":
        """Strictly deserialize the canonical representation; unknown keys fail closed."""

        _strict_keys(cls, payload)
        nested: dict[str, Any] = {}

        data = payload["evidence_subset"]
        _strict_keys(EvidenceSubset, data)
        nested["evidence_subset"] = EvidenceSubset(
            **{**data, "source_ids": tuple(data["source_ids"]), "inclusion_rule_ids": tuple(data["inclusion_rule_ids"]), "exclusion_rule_ids": tuple(data["exclusion_rule_ids"]), "diagnostic_only_source_ids": tuple(data["diagnostic_only_source_ids"]), "scientific_status": ScientificStatus(data["scientific_status"])}
        )

        support_data = payload["target"]["support"]
        _strict_keys(SupportDefinition, support_data)
        target_data = dict(payload["target"])
        target_data["support"] = SupportDefinition(**support_data)
        target_data["allowed_claims"] = tuple(target_data["allowed_claims"])
        target_data["prohibited_claims"] = tuple(target_data["prohibited_claims"])
        target_data["scientific_status"] = ScientificStatus(target_data["scientific_status"])
        _strict_keys(TargetIdentity, target_data)
        nested["target"] = TargetIdentity(**target_data)

        for name in ("independent_unit", "deployment_unit"):
            data = dict(payload[name])
            _strict_keys(UnitDeclaration, data)
            data["key_fields"] = tuple(data["key_fields"])
            data["nesting_fields"] = tuple(data["nesting_fields"])
            data["unresolved_reason_codes"] = tuple(data["unresolved_reason_codes"])
            nested[name] = UnitDeclaration(**data)

        data = dict(payload["preprocessing_validation"])
        _strict_keys(PreprocessingValidation, data)
        data["learned_steps"] = tuple(data["learned_steps"])
        data["leakage_controls"] = tuple(data["leakage_controls"])
        data["authority"] = EvidenceAuthority(data["authority"])
        nested["preprocessing_validation"] = PreprocessingValidation(**data)

        data = dict(payload["method"])
        _strict_keys(MethodSpec, data)
        data["method_ids"] = tuple(data["method_ids"])
        data["baseline_ids"] = tuple(data["baseline_ids"])
        nested["method"] = MethodSpec(**data)

        data = dict(payload["uncertainty_provenance"])
        _strict_keys(UncertaintyProvenance, data)
        data["source_class"] = UncertaintySource(data["source_class"])
        data["assumptions"] = tuple(data["assumptions"])
        data["eligible_uses"] = tuple(data["eligible_uses"])
        data["scientific_status"] = ScientificStatus(data["scientific_status"])
        nested["uncertainty_provenance"] = UncertaintyProvenance(**data)

        data = dict(payload["decision_weighting"])
        _strict_keys(DecisionWeighting, data)
        data["mode"] = WeightingMode(data["mode"])
        data["parameter_refs"] = tuple(data["parameter_refs"])
        nested["decision_weighting"] = DecisionWeighting(**data)

        data = dict(payload["domain_constraints"])
        _strict_keys(DomainConstraints, data)
        data["rule_ids"] = tuple(data["rule_ids"])
        nested["domain_constraints"] = DomainConstraints(**data)

        data = dict(payload["translation_rule"])
        _strict_keys(TranslationRule, data)
        data["allowed_actions"] = tuple(data["allowed_actions"])
        nested["translation_rule"] = TranslationRule(**data)

        data = dict(payload["source_provenance"])
        _strict_keys(SourceProvenance, data)
        data["source_hashes"] = tuple(tuple(item) for item in data["source_hashes"])
        data["lineage"] = tuple(data["lineage"])
        data["origin"] = ArtifactOrigin(data["origin"])
        nested["source_provenance"] = SourceProvenance(**data)

        return cls(
            protocol_id=payload["protocol_id"],
            protocol_version=payload["protocol_version"],
            schema_version=payload["schema_version"],
            task_family=TaskFamily(payload["task_family"]),
            registration_status=RegistrationStatus(payload["registration_status"]),
            origin=ArtifactOrigin(payload["origin"]),
            **nested,
        )
