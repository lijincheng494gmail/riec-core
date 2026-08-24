"""Public RIEC-Core contract surface for the isolated v1.0 RC."""

from .actions import ActionContext, PredictiveActionRecord, SynthesisActionRecord
from .gates import GateDecision, GateEngine, GateResult
from .models import (
    ActionFamily,
    ArtifactOrigin,
    EligibilityState,
    GateState,
    PredictiveAction,
    RegistrationStatus,
    Repairability,
    ScientificStatus,
    SynthesisAction,
    TaskFamily,
)
from .protocol import Protocol
from .v1_contracts import (
    ActionEnvelopeV1,
    ActionQualification,
    AdapterLifecycleV1,
    AggregationEligibility,
    AuditEnvelopeV1,
    CandidateValidityV1,
    ConstraintResultV1,
    GateSemanticBoundaryV1,
    MetricApplicability,
    MetricContractV1,
    MetricValidity,
    OptimizerStatus,
    ReleaseIdentityV1,
    ReleaseStatus,
    ThresholdOwner,
    ThresholdRecordV1,
)

__version__ = "1.0.0-rc.2"

__all__ = [
    "ActionContext",
    "ActionEnvelopeV1",
    "ActionFamily",
    "ActionQualification",
    "AdapterLifecycleV1",
    "AggregationEligibility",
    "ArtifactOrigin",
    "AuditEnvelopeV1",
    "CandidateValidityV1",
    "ConstraintResultV1",
    "EligibilityState",
    "GateDecision",
    "GateEngine",
    "GateResult",
    "GateState",
    "GateSemanticBoundaryV1",
    "MetricApplicability",
    "MetricContractV1",
    "MetricValidity",
    "OptimizerStatus",
    "PredictiveAction",
    "PredictiveActionRecord",
    "Protocol",
    "RegistrationStatus",
    "Repairability",
    "ReleaseIdentityV1",
    "ReleaseStatus",
    "ScientificStatus",
    "SynthesisAction",
    "SynthesisActionRecord",
    "TaskFamily",
    "ThresholdOwner",
    "ThresholdRecordV1",
]
