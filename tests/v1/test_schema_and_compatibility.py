import json
from pathlib import Path
import unittest

import riec_core
from compatibility.migrate_v0_9 import migrate_action, migrate_candidate_validity, migrate_metric_record
from riec_core.v1_contracts import validate_v1_document


ROOT = Path(__file__).resolve().parents[2]


class SchemaAndCompatibilityTests(unittest.TestCase):
    def test_all_schema_json_files_parse(self):
        paths = tuple((ROOT / "schemas").rglob("*.json"))
        self.assertEqual(len(paths), 7)
        for path in paths:
            json.loads(path.read_text(encoding="utf-8"))

    def test_v1_schema_is_release_candidate_not_frozen(self):
        schema = json.loads((ROOT / "schemas" / "v1" / "riec-core-v1-rc.schema.json").read_text(encoding="utf-8"))
        status = schema["properties"]["identity"]["properties"]["status"]["const"]
        self.assertEqual(status, "RELEASE_CANDIDATE_NOT_FROZEN")

    def test_v1_schema_binds_accepted_boundary_hash(self):
        schema = json.loads((ROOT / "schemas" / "v1" / "riec-core-v1-rc.schema.json").read_text(encoding="utf-8"))
        value = schema["properties"]["audit"]["properties"]["post_waiver_boundary_hash"]["const"]
        self.assertEqual(value, "0c51a2877d34bb69165d8b77acffe8534836a5c2e54913f780498da17ca909cf")

    def test_migration_schema_forbids_scientific_change(self):
        schema = json.loads((ROOT / "schemas" / "compatibility" / "v0_9-to-v1-migration.schema.json").read_text(encoding="utf-8"))
        self.assertFalse(schema["properties"]["scientific_values_changed"]["const"])
        self.assertFalse(schema["properties"]["canonical_decision_changed"]["const"])

    def test_minimal_v1_document_passes_dependency_free_validation(self):
        document = json.loads((ROOT / "examples" / "minimal_v1_rc_envelope.json").read_text(encoding="utf-8"))
        validate_v1_document(document)

    def test_final_status_fails_dependency_free_validation(self):
        document = json.loads((ROOT / "examples" / "minimal_v1_rc_envelope.json").read_text(encoding="utf-8"))
        document["identity"]["status"] = "FINAL"
        with self.assertRaises(ValueError):
            validate_v1_document(document)

    def test_negative_result_deletion_fails_validation(self):
        document = json.loads((ROOT / "examples" / "minimal_v1_rc_envelope.json").read_text(encoding="utf-8"))
        document["audit"]["negative_results_retained"] = False
        with self.assertRaises(ValueError):
            validate_v1_document(document)

    def test_public_version_is_rc(self):
        self.assertEqual(riec_core.__version__, "1.0.0-rc.2")

    def test_compatibility_annotation_does_not_change_values_or_action(self):
        metric = migrate_metric_record({"metric_id": "m", "value": 7.5})
        action = migrate_action("ABSTAIN")
        self.assertEqual(metric["original_value"], 7.5)
        self.assertEqual(action.to_legacy(), "ABSTAIN")

    def test_finite_output_does_not_fabricate_optimizer_convergence(self):
        validity = migrate_candidate_validity({"finite_output": True})
        self.assertEqual(validity.optimizer_status.value, "NOT_REPORTED")


if __name__ == "__main__":
    unittest.main()
