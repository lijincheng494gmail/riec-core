import json
import unittest
from dataclasses import fields

from riec_core.protocol import Protocol

from helpers import ROOT


class SchemaContractTests(unittest.TestCase):
    def setUp(self):
        self.schemas = {
            path.name: json.loads(path.read_text(encoding="utf-8"))
            for path in (ROOT / "schemas").glob("*.json")
        }

    def test_all_five_schemas_parse(self):
        self.assertEqual(len(self.schemas), 5)

    def test_all_schemas_declare_draft_2020_12(self):
        self.assertTrue(all(schema["$schema"].endswith("draft/2020-12/schema") for schema in self.schemas.values()))

    def test_protocol_required_fields_match_typed_model(self):
        required = set(self.schemas["protocol.schema.json"]["required"])
        typed = {field.name for field in fields(Protocol)}
        self.assertEqual(required, typed)

    def test_example_has_no_unknown_top_level_fields(self):
        example = json.loads((ROOT / "examples" / "minimal_predictive_protocol.json").read_text(encoding="utf-8"))
        schema = self.schemas["protocol.schema.json"]
        self.assertEqual(set(example), set(schema["required"]))

    def test_example_validates_through_typed_schema(self):
        example = json.loads((ROOT / "examples" / "minimal_predictive_protocol.json").read_text(encoding="utf-8"))
        self.assertEqual(Protocol.from_dict(example).schema_version, "0.1.0")

    def test_gate_schema_has_exact_state_vocabulary(self):
        states = self.schemas["gate-result.schema.json"]["properties"]["state"]["enum"]
        self.assertEqual(states, ["PASS", "WARN", "FAIL", "NOT_EVALUABLE"])

    def test_action_schema_separates_engine_vocabularies(self):
        variants = self.schemas["action.schema.json"]["oneOf"]
        predictive = set(variants[0]["properties"]["action"]["enum"])
        synthesis = set(variants[1]["properties"]["action"]["enum"])
        self.assertNotIn("STRATIFY", predictive)
        self.assertNotIn("SELECT", synthesis)


if __name__ == "__main__":
    unittest.main()
