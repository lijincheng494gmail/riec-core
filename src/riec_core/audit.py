"""Canonical audit-bundle manifest and lineage checks."""

from __future__ import annotations

from dataclasses import dataclass
import re

from .actions import ActionRecord
from .canonical import CanonicalModel, canonical_checksum
from .gates import GateResult
from .protocol import Protocol
from .provenance import AuditRecord, MetricRecord, ProvenanceRecord


_SHA256 = re.compile(r"^[a-f0-9]{64}$")


@dataclass(frozen=True)
class BundleFile(CanonicalModel):
    logical_path: str
    sha256: str
    role: str

    def __post_init__(self) -> None:
        if not self.logical_path or not self.role or not _SHA256.fullmatch(self.sha256):
            raise ValueError("bundle file requires path, role, and SHA-256")


@dataclass(frozen=True)
class AuditBundleManifest(CanonicalModel):
    bundle_id: str
    bundle_version: str
    run_manifest_hash: str
    protocol_checksums: tuple[str, ...]
    gate_snapshot_hashes: tuple[str, ...]
    action_ids: tuple[str, ...]
    metric_ids: tuple[str, ...]
    provenance_record_ids: tuple[str, ...]
    files: tuple[BundleFile, ...]
    canonical: bool

    def __post_init__(self) -> None:
        if not self.bundle_id or not self.bundle_version:
            raise ValueError("bundle identity is required")
        if not _SHA256.fullmatch(self.run_manifest_hash):
            raise ValueError("run_manifest_hash must be SHA-256")
        if len(set(file.logical_path for file in self.files)) != len(self.files):
            raise ValueError("bundle logical paths must be unique")


def validate_lineage(
    protocols: tuple[Protocol, ...],
    gates: tuple[GateResult, ...],
    actions: tuple[ActionRecord, ...],
    metrics: tuple[MetricRecord, ...],
    provenance: tuple[ProvenanceRecord, ...],
    audit_events: tuple[AuditRecord, ...],
) -> tuple[str, ...]:
    errors: list[str] = []
    protocol_hashes = {protocol.checksum() for protocol in protocols}
    gate_hashes = {canonical_checksum(gates)} if gates else set()
    action_ids = {action.context.action_id for action in actions}
    provenance_ids = {record.record_id for record in provenance}

    for action in actions:
        if action.context.protocol_checksum not in protocol_hashes:
            errors.append(f"action {action.context.action_id} has unknown protocol checksum")
        if action.context.gate_snapshot_hash not in gate_hashes:
            errors.append(f"action {action.context.action_id} has unknown gate snapshot")
    for metric in metrics:
        if metric.action_id is not None and metric.action_id not in action_ids:
            errors.append(f"metric {metric.metric_id} has unknown action")
    for event in audit_events:
        for ref in event.object_refs:
            if ref not in action_ids and ref not in provenance_ids:
                errors.append(f"audit event {event.event_id} has unknown object ref {ref}")
    return tuple(errors)
