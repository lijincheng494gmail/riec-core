"""Deterministic serialization and checksums for canonical Core objects."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
import math
from typing import Any, Mapping


class CanonicalizationError(ValueError):
    """Raised when a value cannot be represented canonically."""


def canonical_data(value: Any) -> Any:
    """Convert typed objects to a stable JSON-compatible structure."""

    if is_dataclass(value):
        return {field.name: canonical_data(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise CanonicalizationError("naive datetime is not canonical")
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(value, Mapping):
        if not all(isinstance(key, str) for key in value):
            raise CanonicalizationError("canonical mapping keys must be strings")
        return {key: canonical_data(value[key]) for key in sorted(value)}
    if isinstance(value, (tuple, list)):
        return [canonical_data(item) for item in value]
    if isinstance(value, float):
        if not math.isfinite(value):
            raise CanonicalizationError("non-finite floats are forbidden")
        return 0.0 if value == 0.0 else value
    if value is None or isinstance(value, (str, int, bool)):
        return value
    raise CanonicalizationError(f"unsupported canonical type: {type(value).__name__}")


def canonical_json(value: Any) -> str:
    return json.dumps(
        canonical_data(value),
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def canonical_checksum(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


class CanonicalModel:
    """Mixin for typed immutable records."""

    def to_dict(self) -> dict[str, Any]:
        data = canonical_data(self)
        if not isinstance(data, dict):
            raise CanonicalizationError("canonical model did not serialize to an object")
        return data

    def to_json(self) -> str:
        return canonical_json(self)

    def checksum(self) -> str:
        return canonical_checksum(self)
