"""Typed provenance, audit, and metric records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import re

from .canonical import CanonicalModel
from .models import ArtifactOrigin, ScientificStatus


_SHA256 = re.compile(r"^[a-f0-9]{64}$")


def _hash(value: str, field_name: str) -> None:
    if not _SHA256.fullmatch(value):
        raise ValueError(f"{field_name} must be SHA-256")


@dataclass(frozen=True)
class EvidenceIdentity(CanonicalModel):
    evidence_id: str
    evidence_version: str
    source_id: str
    content_hash: str
    origin: ArtifactOrigin
    scientific_status: ScientificStatus

    def __post_init__(self) -> None:
        if not self.evidence_id or not self.evidence_version or not self.source_id:
            raise ValueError("evidence identity fields are required")
        _hash(self.content_hash, "content_hash")


@dataclass(frozen=True)
class ProvenanceRecord(CanonicalModel):
    record_id: str
    record_version: str
    object_id: str
    source_refs: tuple[str, ...]
    content_hash: str
    origin: ArtifactOrigin
    scientific_status: ScientificStatus
    created_at: datetime
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.record_id or not self.object_id or not self.source_refs:
            raise ValueError("provenance requires record, object, and source references")
        _hash(self.content_hash, "content_hash")
        if self.created_at.tzinfo is None:
            raise ValueError("provenance timestamp must be timezone-aware")


@dataclass(frozen=True)
class AuditRecord(CanonicalModel):
    event_id: str
    event_version: str
    event_type: str
    object_refs: tuple[str, ...]
    reason_codes: tuple[str, ...]
    config_hash: str
    created_at: datetime
    origin: ArtifactOrigin

    def __post_init__(self) -> None:
        if not self.event_id or not self.event_type or not self.object_refs or not self.reason_codes:
            raise ValueError("audit event identity, object refs, and reason codes are required")
        _hash(self.config_hash, "config_hash")
        if self.created_at.tzinfo is None:
            raise ValueError("audit timestamp must be timezone-aware")


@dataclass(frozen=True)
class MetricRecord(CanonicalModel):
    metric_id: str
    metric_version: str
    target_scope: str
    numerator: float
    denominator: int
    unit: str
    direction: str
    panel: str
    independent_unit: str
    source_fingerprint: str
    action_id: str | None
    origin: ArtifactOrigin

    def __post_init__(self) -> None:
        if self.denominator <= 0:
            raise ValueError("metric denominator must be positive; empty panels are NOT_EVALUABLE")
        if not all((self.metric_id, self.metric_version, self.unit, self.panel, self.independent_unit)):
            raise ValueError("metric identity, unit, panel, and independent unit are required")
        _hash(self.source_fingerprint, "source_fingerprint")
