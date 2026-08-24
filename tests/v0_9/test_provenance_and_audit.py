import unittest

from riec_core.audit import AuditBundleManifest, BundleFile, validate_lineage
from riec_core.canonical import canonical_checksum
from riec_core.engines.predictive import AbsoluteTolerancePolicy, DecisionOrder, PredictiveEngine
from riec_core.models import ArtifactOrigin, ScientificStatus
from riec_core.provenance import AuditRecord, MetricRecord, ProvenanceRecord

from helpers import FIXED_TIME, candidate, load_predictive_protocol, pass_gates


class ProvenanceAndAuditTests(unittest.TestCase):
    def setUp(self):
        self.protocol = load_predictive_protocol()
        self.gates = pass_gates()
        self.decision = PredictiveEngine.decide(
            self.protocol, (candidate("a", 1.0),), self.gates, AbsoluteTolerancePolicy(0.0),
            DecisionOrder("order", "0.1.0", ("primary_risk",)), timestamp=FIXED_TIME,
        )
        self.provenance = ProvenanceRecord(
            "prov-1", "0.1.0", "source-object", ("source:synthetic",), canonical_checksum({"source": 1}),
            ArtifactOrigin.NEW_ARCHITECTURE_PROPOSAL, ScientificStatus.VERIFIED, FIXED_TIME,
        )

    def test_valid_lineage_reconstructs(self):
        metric = MetricRecord(
            "risk", "0.1.0", "synthetic", 1.0, 4, "unit", "lower", "synthetic", "group",
            canonical_checksum({"source": 1}), self.decision.action_record.context.action_id, ArtifactOrigin.RUNTIME_RESULT,
        )
        event = AuditRecord(
            "event-1", "0.1.0", "ACTION_EMITTED", (self.decision.action_record.context.action_id,),
            ("SYNTHETIC",), canonical_checksum({"config": 1}), FIXED_TIME, ArtifactOrigin.RUNTIME_RESULT,
        )
        errors = validate_lineage(
            (self.protocol,), self.gates, (self.decision.action_record,), (metric,), (self.provenance,), (event,)
        )
        self.assertEqual(errors, ())

    def test_missing_protocol_breaks_reconstruction(self):
        errors = validate_lineage((), self.gates, (self.decision.action_record,), (), (self.provenance,), ())
        self.assertTrue(any("unknown protocol" in error for error in errors))

    def test_missing_action_breaks_metric_lineage(self):
        metric = MetricRecord(
            "risk", "0.1.0", "synthetic", 1.0, 4, "unit", "lower", "synthetic", "group",
            canonical_checksum({"source": 1}), "unknown-action", ArtifactOrigin.RUNTIME_RESULT,
        )
        errors = validate_lineage((self.protocol,), self.gates, (), (metric,), (self.provenance,), ())
        self.assertTrue(any("unknown action" in error for error in errors))

    def test_metric_empty_denominator_is_rejected(self):
        with self.assertRaises(ValueError):
            MetricRecord("m", "0.1.0", "x", 0, 0, "unit", "lower", "panel", "unit", "0" * 64, None, ArtifactOrigin.RUNTIME_RESULT)

    def test_duplicate_bundle_paths_are_rejected(self):
        file = BundleFile("ACTIONS.jsonl", "0" * 64, "actions")
        with self.assertRaises(ValueError):
            AuditBundleManifest("b", "0.1.0", "0" * 64, (), (), (), (), (), (file, file), False)

    def test_bundle_can_remain_noncanonical(self):
        bundle = AuditBundleManifest("b", "0.1.0", "0" * 64, (), (), (), (), (), (), False)
        self.assertFalse(bundle.canonical)

    def test_provenance_origin_is_not_runtime_result(self):
        self.assertEqual(self.provenance.origin, ArtifactOrigin.NEW_ARCHITECTURE_PROPOSAL)


if __name__ == "__main__":
    unittest.main()
