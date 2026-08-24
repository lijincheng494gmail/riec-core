"""Strict, fail-closed JSON configuration loading."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from .canonical import CanonicalModel, canonical_data
from .models import ArtifactOrigin


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class LoadedConfig(CanonicalModel):
    config_id: str
    config_version: str
    values: tuple[tuple[str, Any], ...]
    origin: ArtifactOrigin = ArtifactOrigin.CONFIGURATION

    def get(self, key: str) -> Any:
        for item_key, value in self.values:
            if item_key == key:
                return value
        raise KeyError(key)


class StrictConfigLoader:
    @staticmethod
    def load(path: str | Path, *, required: set[str], optional: set[str] | None = None) -> LoadedConfig:
        config_path = Path(path)
        if config_path.suffix.lower() != ".json":
            raise ConfigError("Phase 3 strict loader accepts JSON only")
        try:
            payload = json.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ConfigError(f"invalid configuration: {error}") from error
        if not isinstance(payload, dict):
            raise ConfigError("configuration root must be an object")
        optional = optional or set()
        allowed = required | optional
        missing = required - set(payload)
        extra = set(payload) - allowed
        if missing or extra:
            raise ConfigError(f"configuration keys mismatch; missing={sorted(missing)}; extra={sorted(extra)}")
        config_id = payload.get("config_id")
        config_version = payload.get("config_version")
        if not isinstance(config_id, str) or not config_id or not isinstance(config_version, str) or not config_version:
            raise ConfigError("config_id and config_version are required strings")
        values = tuple((key, canonical_data(payload[key])) for key in sorted(payload))
        return LoadedConfig(config_id, config_version, values)
