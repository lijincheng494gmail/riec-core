"""Freeze records and mutation detection. No v1.0 freeze is created here."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .canonical import CanonicalModel, canonical_checksum
from .models import ArtifactOrigin


class FreezeState(str, Enum):
    DRAFT = "DRAFT"
    SEALED = "SEALED"
    INVALIDATED = "INVALIDATED"


class AmendmentClass(str, Enum):
    TECHNICAL_FIX = "TECHNICAL_FIX"
    SUBSTANTIVE_CHANGE = "SUBSTANTIVE_CHANGE"


class SubstantiveMutationError(RuntimeError):
    pass


@dataclass(frozen=True)
class FreezeRecord(CanonicalModel):
    freeze_id: str
    freeze_version: str
    state: FreezeState
    semantic_payload_hash: str
    allowed_nonsemantic_fields: tuple[str, ...]
    oracle_opened: bool
    origin: ArtifactOrigin

    @classmethod
    def draft(cls, freeze_id: str, freeze_version: str, semantic_payload: object) -> "FreezeRecord":
        return cls(
            freeze_id=freeze_id,
            freeze_version=freeze_version,
            state=FreezeState.DRAFT,
            semantic_payload_hash=canonical_checksum(semantic_payload),
            allowed_nonsemantic_fields=("output_path", "timestamp", "hardware_telemetry"),
            oracle_opened=False,
            origin=ArtifactOrigin.NEW_ARCHITECTURE_PROPOSAL,
        )


class FreezeGuard:
    @staticmethod
    def assert_semantic_unchanged(record: FreezeRecord, candidate_payload: object) -> None:
        candidate_hash = canonical_checksum(candidate_payload)
        if candidate_hash != record.semantic_payload_hash:
            raise SubstantiveMutationError(
                f"semantic payload changed for freeze {record.freeze_id}; a new freeze is required"
            )

    @staticmethod
    def classify_change(*, semantic_hash_changed: bool, outcome_informed: bool) -> AmendmentClass:
        if semantic_hash_changed or outcome_informed:
            return AmendmentClass.SUBSTANTIVE_CHANGE
        return AmendmentClass.TECHNICAL_FIX
