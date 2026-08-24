import json
import unittest
from dataclasses import replace

from riec_core.canonical import CanonicalizationError, canonical_checksum, canonical_json
from riec_core.models import ArtifactOrigin, RegistrationStatus, ScientificStatus, WeightingMode
from riec_core.protocol import DecisionWeighting, Protocol, UnitDeclaration

from helpers import ROOT, load_predictive_protocol


class ProtocolTests(unittest.TestCase):
    def test_protocol_instantiates(self):
        protocol = load_predictive_protocol()
        self.assertEqual(protocol.protocol_id, "synthetic.predictive.minimum")

    def test_roundtrip_serialization_is_exact(self):
        protocol = load_predictive_protocol()
        restored = Protocol.from_dict(json.loads(protocol.to_json()))
        self.assertEqual(restored, protocol)

    def test_checksum_is_deterministic(self):
        protocol = load_predictive_protocol()
        self.assertEqual(protocol.checksum(), Protocol.from_dict(protocol.to_dict()).checksum())

    def test_version_is_explicit(self):
        protocol = load_predictive_protocol()
        with self.assertRaises(ValueError):
            replace(protocol, protocol_version="latest")

    def test_unknown_protocol_key_is_rejected(self):
        payload = load_predictive_protocol().to_dict()
        payload["unexpected"] = True
        with self.assertRaises(ValueError):
            Protocol.from_dict(payload)

    def test_registered_protocol_requires_freeze_reference(self):
        protocol = load_predictive_protocol()
        source = replace(protocol.source_provenance, freeze_id=None)
        with self.assertRaises(ValueError):
            replace(protocol, source_provenance=source, registration_status=RegistrationStatus.REGISTERED)

    def test_weighting_modes_do_not_collapse(self):
        protocol = load_predictive_protocol()
        weighting = DecisionWeighting("0.1.0", WeightingMode.EVIDENCE_WEIGHTING, "bad", ())
        with self.assertRaises(ValueError):
            replace(protocol, decision_weighting=weighting)

    def test_unresolved_unit_is_serializable(self):
        unit = UnitDeclaration("0.1.0", "UNDEFINED", (), (), "flat", True, ("UNIT.UNKNOWN",))
        self.assertIn("UNIT.UNKNOWN", unit.to_json())

    def test_origins_are_explicit(self):
        protocol = load_predictive_protocol()
        self.assertEqual(protocol.origin, ArtifactOrigin.NEW_ARCHITECTURE_PROPOSAL)
        self.assertEqual(protocol.evidence_subset.scientific_status, ScientificStatus.VERIFIED)

    def test_nonfinite_value_is_not_canonical(self):
        with self.assertRaises(CanonicalizationError):
            canonical_json({"value": float("nan")})

    def test_schema_file_is_valid_json(self):
        schema = json.loads((ROOT / "schemas" / "protocol.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["schema_version"]["const"], "0.1.0")

    def test_canonical_dict_order_does_not_change_hash(self):
        self.assertEqual(canonical_checksum({"a": 1, "b": 2}), canonical_checksum({"b": 2, "a": 1}))


if __name__ == "__main__":
    unittest.main()
