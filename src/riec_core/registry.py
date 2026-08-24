"""Typed registries for immutable Core definitions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from .canonical import CanonicalModel, canonical_checksum
from .models import ArtifactOrigin, ScientificStatus


T = TypeVar("T")


class RegistryError(ValueError):
    pass


@dataclass(frozen=True)
class RegistryEntry(CanonicalModel):
    key: str
    version: str
    kind: str
    payload_checksum: str
    origin: ArtifactOrigin
    scientific_status: ScientificStatus


class Registry(Generic[T]):
    def __init__(self, kind: str) -> None:
        if not kind:
            raise ValueError("registry kind is required")
        self.kind = kind
        self._entries: dict[tuple[str, str], tuple[RegistryEntry, T]] = {}

    def register(
        self,
        key: str,
        version: str,
        payload: T,
        *,
        origin: ArtifactOrigin,
        scientific_status: ScientificStatus,
    ) -> RegistryEntry:
        identity = (key, version)
        checksum = canonical_checksum(payload)
        entry = RegistryEntry(key, version, self.kind, checksum, origin, scientific_status)
        if identity in self._entries:
            existing, _ = self._entries[identity]
            if existing.payload_checksum != checksum:
                raise RegistryError(f"conflicting payload for {self.kind}:{key}@{version}")
            return existing
        self._entries[identity] = (entry, payload)
        return entry

    def resolve(self, key: str, version: str) -> T:
        try:
            return self._entries[(key, version)][1]
        except KeyError as error:
            raise RegistryError(f"unknown {self.kind}:{key}@{version}") from error

    def entry(self, key: str, version: str) -> RegistryEntry:
        try:
            return self._entries[(key, version)][0]
        except KeyError as error:
            raise RegistryError(f"unknown {self.kind}:{key}@{version}") from error

    def entries(self) -> tuple[RegistryEntry, ...]:
        return tuple(self._entries[key][0] for key in sorted(self._entries))

    def snapshot_checksum(self) -> str:
        return canonical_checksum(self.entries())


@dataclass(frozen=True)
class MetricDefinition(CanonicalModel):
    metric_id: str
    metric_version: str
    name: str
    unit: str
    panel: str
    denominator_definition: str
    direction: str
    truth_required: bool
    origin: ArtifactOrigin

    def __post_init__(self) -> None:
        if not all((self.metric_id, self.metric_version, self.name, self.unit, self.panel, self.denominator_definition)):
            raise ValueError("metric identity, panel, unit, and denominator are required")


@dataclass(frozen=True)
class GateDefinition(CanonicalModel):
    gate_id: str
    gate_version: str
    name: str
    non_compensatory: bool
    origin: ArtifactOrigin

    def __post_init__(self) -> None:
        if not self.non_compensatory:
            raise ValueError("Core eligibility gates must be non-compensatory")


@dataclass(frozen=True)
class NamedDefinition(CanonicalModel):
    definition_id: str
    version: str
    definition_kind: str
    description: str
    origin: ArtifactOrigin


class CoreRegistries:
    """Explicit registry set; outcomes cannot mutate registered payloads."""

    def __init__(self) -> None:
        self.protocols: Registry[Any] = Registry("protocol")
        self.metrics: Registry[MetricDefinition] = Registry("metric")
        self.gates: Registry[GateDefinition] = Registry("gate")
        self.rules: Registry[NamedDefinition] = Registry("rule")
        self.reason_codes: Registry[NamedDefinition] = Registry("reason_code")
        self.policies: Registry[NamedDefinition] = Registry("policy")
        self.freezes: Registry[Any] = Registry("freeze")

    def snapshot_checksum(self) -> str:
        return canonical_checksum(
            {
                "protocols": self.protocols.entries(),
                "metrics": self.metrics.entries(),
                "gates": self.gates.entries(),
                "rules": self.rules.entries(),
                "reason_codes": self.reason_codes.entries(),
                "policies": self.policies.entries(),
                "freezes": self.freezes.entries(),
            }
        )
