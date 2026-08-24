"""Shared enums. No domain adapter name or rule is defined here."""

from enum import Enum


class ArtifactOrigin(str, Enum):
    HISTORICAL_FACT = "HISTORICAL_FACT"
    NEW_ARCHITECTURE_PROPOSAL = "NEW_ARCHITECTURE_PROPOSAL"
    CONFIGURATION = "CONFIGURATION"
    RUNTIME_RESULT = "RUNTIME_RESULT"


class ScientificStatus(str, Enum):
    VERIFIED = "VERIFIED"
    UNRESOLVED_SEMANTICS = "UNRESOLVED_SEMANTICS"
    UNVERIFIED_PROVENANCE = "UNVERIFIED_PROVENANCE"
    REQUIRES_RECONCILIATION = "REQUIRES_RECONCILIATION"
    NOT_EVALUABLE = "NOT_EVALUABLE"
    NOT_STARTED = "NOT_STARTED"
    LOCKBOX_NOT_OPENED = "LOCKBOX_NOT_OPENED"
    MIGRATION_SCAFFOLD = "MIGRATION_SCAFFOLD"


class TaskFamily(str, Enum):
    PREDICTIVE_SELECTION = "predictive_selection"
    EVIDENCE_SYNTHESIS = "evidence_synthesis"


class RegistrationStatus(str, Enum):
    UNREGISTERED = "UNREGISTERED"
    REGISTERED = "REGISTERED"
    QUARANTINED = "QUARANTINED"
    REJECTED = "REJECTED"


class GateState(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    NOT_EVALUABLE = "NOT_EVALUABLE"


class EligibilityState(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    CONDITIONALLY_ELIGIBLE = "CONDITIONALLY_ELIGIBLE"
    INELIGIBLE = "INELIGIBLE"
    NOT_EVALUABLE = "NOT_EVALUABLE"


class Repairability(str, Enum):
    DATA_CORRECTABLE = "DATA_CORRECTABLE"
    EVIDENCE_ACQUIRABLE = "EVIDENCE_ACQUIRABLE"
    POLICY_AMENDMENT_REQUIRED = "POLICY_AMENDMENT_REQUIRED"
    INTRINSIC_INCOMPATIBILITY = "INTRINSIC_INCOMPATIBILITY"
    POST_FREEZE_FORBIDDEN = "POST_FREEZE_FORBIDDEN"


class ActionFamily(str, Enum):
    COMMIT = "COMMIT"
    PARTITION = "PARTITION"
    BOUND = "BOUND"
    NON_DECISION = "NON_DECISION"
    DIAGNOSTIC_ONLY = "DIAGNOSTIC_ONLY"


class PredictiveAction(str, Enum):
    SELECT = "SELECT"
    SELECT_WITH_CONDITIONS = "SELECT_WITH_CONDITIONS"
    FALLBACK_SELECT = "FALLBACK_SELECT"
    ABSTAIN = "ABSTAIN"
    DIAGNOSTIC_ONLY = "DIAGNOSTIC_ONLY"


class SynthesisAction(str, Enum):
    RESOLVE = "RESOLVE"
    STRATIFY = "STRATIFY"
    DOWNGRADE = "DOWNGRADE"
    ABSTAIN = "ABSTAIN"
    DIAGNOSTIC_ONLY = "DIAGNOSTIC_ONLY"


class EvidenceAuthority(str, Enum):
    FORMAL = "formal"
    SECONDARY = "secondary"
    STRESS = "stress"
    DIAGNOSTIC_ONLY = "diagnostic_only"


class WeightingMode(str, Enum):
    NONE = "none"
    DECISION_COSTS = "decision_costs"
    EVIDENCE_WEIGHTING = "evidence_weighting"


class UncertaintySource(str, Enum):
    OBSERVED = "observed"
    MODEL_BASED = "model_based"
    RESAMPLING = "resampling"
    DERIVED = "derived"
    UNAVAILABLE = "unavailable"
    NOT_APPLICABLE = "not_applicable"
