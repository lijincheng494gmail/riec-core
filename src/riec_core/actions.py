"""Task-specific actions inside a common typed envelope."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import re

from .canonical import CanonicalModel
from .models import (
    ActionFamily,
    ArtifactOrigin,
    PredictiveAction,
    SynthesisAction,
)


_SHA256 = re.compile(r"^[a-f0-9]{64}$")


@dataclass(frozen=True)
class ActionContext(CanonicalModel):
    action_id: str
    protocol_checksum: str
    gate_snapshot_hash: str
    policy_version: str
    reason_codes: tuple[str, ...]
    conditions: tuple[str, ...]
    selected_object_ids: tuple[str, ...]
    claim_scope: str | None
    timestamp: datetime
    origin: ArtifactOrigin = ArtifactOrigin.RUNTIME_RESULT

    def __post_init__(self) -> None:
        if not self.action_id or not self.policy_version or not self.reason_codes:
            raise ValueError("action identity, policy version, and reason codes are required")
        if not _SHA256.fullmatch(self.protocol_checksum) or not _SHA256.fullmatch(self.gate_snapshot_hash):
            raise ValueError("action checksum fields must be SHA-256")
        if self.timestamp.tzinfo is None:
            raise ValueError("action timestamp must be timezone-aware")


_PREDICTIVE_FAMILY = {
    PredictiveAction.SELECT: ActionFamily.COMMIT,
    PredictiveAction.SELECT_WITH_CONDITIONS: ActionFamily.BOUND,
    PredictiveAction.FALLBACK_SELECT: ActionFamily.BOUND,
    PredictiveAction.ABSTAIN: ActionFamily.NON_DECISION,
    PredictiveAction.DIAGNOSTIC_ONLY: ActionFamily.DIAGNOSTIC_ONLY,
}


@dataclass(frozen=True)
class PredictiveActionRecord(CanonicalModel):
    context: ActionContext
    action: PredictiveAction
    family: ActionFamily

    def __post_init__(self) -> None:
        if self.family is not _PREDICTIVE_FAMILY[self.action]:
            raise ValueError("predictive action/family mismatch")
        if self.action in {PredictiveAction.SELECT, PredictiveAction.SELECT_WITH_CONDITIONS, PredictiveAction.FALLBACK_SELECT} and len(self.context.selected_object_ids) != 1:
            raise ValueError("predictive commitment must select exactly one object")
        if self.action is PredictiveAction.ABSTAIN and self.context.selected_object_ids:
            raise ValueError("ABSTAIN cannot select an object")
        if self.action is PredictiveAction.SELECT_WITH_CONDITIONS and not self.context.conditions:
            raise ValueError("conditional selection requires conditions")


_SYNTHESIS_FAMILY = {
    SynthesisAction.RESOLVE: ActionFamily.COMMIT,
    SynthesisAction.STRATIFY: ActionFamily.PARTITION,
    SynthesisAction.DOWNGRADE: ActionFamily.BOUND,
    SynthesisAction.ABSTAIN: ActionFamily.NON_DECISION,
    SynthesisAction.DIAGNOSTIC_ONLY: ActionFamily.DIAGNOSTIC_ONLY,
}


@dataclass(frozen=True)
class SynthesisActionRecord(CanonicalModel):
    context: ActionContext
    action: SynthesisAction
    family: ActionFamily

    def __post_init__(self) -> None:
        if self.family is not _SYNTHESIS_FAMILY[self.action]:
            raise ValueError("synthesis action/family mismatch")
        if self.action is SynthesisAction.DOWNGRADE and not self.context.claim_scope:
            raise ValueError("DOWNGRADE must name the bounded claim scope")
        if self.action is SynthesisAction.STRATIFY and len(self.context.selected_object_ids) < 2:
            raise ValueError("STRATIFY must expose at least two partitions")
        if self.action is SynthesisAction.ABSTAIN and self.context.selected_object_ids:
            raise ValueError("ABSTAIN cannot select evidence objects")


ActionRecord = PredictiveActionRecord | SynthesisActionRecord
