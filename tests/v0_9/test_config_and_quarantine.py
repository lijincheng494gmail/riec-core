import json
import tempfile
import unittest
from pathlib import Path

from riec_core.config import ConfigError, StrictConfigLoader
from riec_core.models import ArtifactOrigin, ScientificStatus
from riec_core.quarantine import QuarantineCatalog

from helpers import ROOT


class ConfigAndQuarantineTests(unittest.TestCase):
    def test_core_config_loads_strictly(self):
        required = {
            "config_id", "config_version", "origin", "architecture_status", "implementation_mode",
            "freeze_ready", "historical_benchmarks_allowed", "formal_benchmark_allowed",
        }
        config = StrictConfigLoader.load(ROOT / "configs" / "development" / "core.json", required=required)
        self.assertEqual(config.origin, ArtifactOrigin.CONFIGURATION)
        self.assertFalse(config.get("freeze_ready"))

    def test_invalid_json_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "bad.json"
            path.write_text("{bad", encoding="utf-8")
            with self.assertRaises(ConfigError):
                StrictConfigLoader.load(path, required={"config_id", "config_version"})

    def test_unknown_config_key_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "bad.json"
            path.write_text('{"config_id":"x","config_version":"0.1.0","extra":1}', encoding="utf-8")
            with self.assertRaises(ConfigError):
                StrictConfigLoader.load(path, required={"config_id", "config_version"})

    def test_non_json_config_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "bad.yaml"
            path.write_text("config_id: x", encoding="utf-8")
            with self.assertRaises(ConfigError):
                StrictConfigLoader.load(path, required={"config_id", "config_version"})

    def test_all_29_discrepancies_are_typed(self):
        catalog = QuarantineCatalog.load(ROOT / "configs" / "quarantine" / "discrepancies.json")
        self.assertEqual(len(catalog.records), 29)
        self.assertTrue(all(record.origin is ArtifactOrigin.HISTORICAL_FACT for record in catalog.records))

    def test_three_high_critical_discrepancies_have_blocking_states(self):
        catalog = QuarantineCatalog.load(ROOT / "configs" / "quarantine" / "discrepancies.json")
        expected = {"D-D004", "D-D012", "E-D007"}
        actual = {record.discrepancy_id for record in catalog.records if record.impact in {"HIGH", "CRITICAL"}}
        self.assertEqual(actual, expected)
        self.assertEqual(catalog.get("D-D012").scientific_status, ScientificStatus.UNRESOLVED_SEMANTICS)
        self.assertEqual(catalog.get("E-D007").scientific_status, ScientificStatus.UNVERIFIED_PROVENANCE)

    def test_inheritance_policy_counts_are_consistent(self):
        payload = json.loads((ROOT / "configs" / "migration" / "inheritance_policy.json").read_text(encoding="utf-8"))
        self.assertEqual(sum(payload["counts"].values()), 42)
        self.assertEqual(len(payload["active_universal_candidates"]), 17)
        self.assertEqual(len(payload["requires_reconciliation"]), 8)
        self.assertEqual(len(payload["domain_only"]), 11)
        self.assertEqual(len(payload["do_not_inherit"]), 6)

    def test_lockbox_config_is_closed(self):
        payload = json.loads((ROOT / "configs" / "lockbox" / "LOCKBOX_CLOSED.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["status"], "LOCKBOX_NOT_OPENED")
        self.assertFalse(payload["oracle_accessed"])


if __name__ == "__main__":
    unittest.main()
