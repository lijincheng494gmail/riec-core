import unittest

from riec_core.models import ArtifactOrigin, ScientificStatus
from riec_core.registry import CoreRegistries, MetricDefinition, Registry, RegistryError

from helpers import load_predictive_protocol


class RegistryTests(unittest.TestCase):
    def test_register_and_resolve_typed_payload(self):
        registry = Registry("protocol")
        protocol = load_predictive_protocol()
        registry.register(
            protocol.protocol_id,
            protocol.protocol_version,
            protocol,
            origin=protocol.origin,
            scientific_status=ScientificStatus.VERIFIED,
        )
        self.assertIs(registry.resolve(protocol.protocol_id, protocol.protocol_version), protocol)

    def test_conflicting_same_version_is_rejected(self):
        registry = Registry("definition")
        registry.register("x", "0.1.0", {"value": 1}, origin=ArtifactOrigin.CONFIGURATION, scientific_status=ScientificStatus.VERIFIED)
        with self.assertRaises(RegistryError):
            registry.register("x", "0.1.0", {"value": 2}, origin=ArtifactOrigin.CONFIGURATION, scientific_status=ScientificStatus.VERIFIED)

    def test_idempotent_registration_is_allowed(self):
        registry = Registry("definition")
        first = registry.register("x", "0.1.0", {"value": 1}, origin=ArtifactOrigin.CONFIGURATION, scientific_status=ScientificStatus.VERIFIED)
        second = registry.register("x", "0.1.0", {"value": 1}, origin=ArtifactOrigin.CONFIGURATION, scientific_status=ScientificStatus.VERIFIED)
        self.assertEqual(first, second)

    def test_metric_requires_panel_and_denominator(self):
        with self.assertRaises(ValueError):
            MetricDefinition("m", "0.1.0", "metric", "unit", "", "", "lower", False, ArtifactOrigin.CONFIGURATION)

    def test_registry_snapshot_is_deterministic(self):
        left = Registry("definition")
        right = Registry("definition")
        for key in ("b", "a"):
            left.register(key, "0.1.0", {"key": key}, origin=ArtifactOrigin.CONFIGURATION, scientific_status=ScientificStatus.VERIFIED)
        for key in ("a", "b"):
            right.register(key, "0.1.0", {"key": key}, origin=ArtifactOrigin.CONFIGURATION, scientific_status=ScientificStatus.VERIFIED)
        self.assertEqual(left.snapshot_checksum(), right.snapshot_checksum())

    def test_core_has_all_required_registries(self):
        registries = CoreRegistries()
        for name in ("protocols", "metrics", "gates", "rules", "reason_codes", "policies", "freezes"):
            self.assertTrue(hasattr(registries, name))


if __name__ == "__main__":
    unittest.main()
