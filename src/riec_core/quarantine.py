"""Executable representation of unresolved discrepancy states."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from .canonical import CanonicalModel
from .models import ArtifactOrigin, ScientificStatus


@dataclass(frozen=True)
class QuarantineRecord(CanonicalModel):
    discrepancy_id: str
    source_project: str
    impact: str
    inheritance_status: str
    scientific_status: ScientificStatus
    blocking_scopes: tuple[str, ...]
    required_action: str
    origin: ArtifactOrigin

    def __post_init__(self) -> None:
        if not all((self.discrepancy_id, self.source_project, self.impact, self.inheritance_status, self.required_action)):
            raise ValueError("complete quarantine identity and disposition are required")


class QuarantineCatalog:
    def __init__(self, records: tuple[QuarantineRecord, ...]) -> None:
        ids = [record.discrepancy_id for record in records]
        if len(set(ids)) != len(ids):
            raise ValueError("duplicate discrepancy IDs")
        self.records = tuple(sorted(records, key=lambda record: record.discrepancy_id))

    @classmethod
    def load(cls, path: str | Path) -> "QuarantineCatalog":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if set(payload) != {"catalog_id", "catalog_version", "origin", "records"}:
            raise ValueError("invalid quarantine catalog keys")
        if payload["origin"] != ArtifactOrigin.CONFIGURATION.value:
            raise ValueError("quarantine catalog must be CONFIGURATION")
        records = tuple(
            QuarantineRecord(
                discrepancy_id=item["discrepancy_id"],
                source_project=item["source_project"],
                impact=item["impact"],
                inheritance_status=item["inheritance_status"],
                scientific_status=ScientificStatus(item["scientific_status"]),
                blocking_scopes=tuple(item["blocking_scopes"]),
                required_action=item["required_action"],
                origin=ArtifactOrigin(item["origin"]),
            )
            for item in payload["records"]
        )
        return cls(records)

    def get(self, discrepancy_id: str) -> QuarantineRecord:
        for record in self.records:
            if record.discrepancy_id == discrepancy_id:
                return record
        raise KeyError(discrepancy_id)

    def by_project(self, source_project: str) -> tuple[QuarantineRecord, ...]:
        return tuple(record for record in self.records if record.source_project == source_project)
