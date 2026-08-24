import unittest

from compatibility.migrate_v0_9 import migrate_candidate_validity, migrate_metric_record
from riec_core.models import GateState
from riec_core.v1_contracts import (
    AggregationEligibility,
    CandidateValidityV1,
    MetricApplicability,
    MetricContractV1,
    MetricValidity,
    OptimizerStatus,
)


class MetricContractTests(unittest.TestCase):
    def test_evaluable_metric_contract(self):
        record = MetricContractV1(
            "loss.mae", True, MetricApplicability.EVALUABLE, MetricValidity.VALID,
            AggregationEligibility.INCLUDE, "mean_over_registered_units", "error_if_missing", "absolute_error",
        )
        self.assertEqual(record.validity, MetricValidity.VALID)

    def test_constant_target_r2_is_not_evaluable(self):
        record = MetricContractV1(
            "metric.r2", True, MetricApplicability.NOT_EVALUABLE, MetricValidity.NOT_EVALUABLE,
            AggregationEligibility.EXCLUDE_UNDEFINED_ONLY, "exclude_r2_only_retain_lane", "constant_target", None,
        )
        self.assertEqual(record.applicability, MetricApplicability.NOT_EVALUABLE)

    def test_absent_metric_cannot_be_applicable(self):
        with self.assertRaises(ValueError):
            MetricContractV1(
                "missing", False, MetricApplicability.EVALUABLE, MetricValidity.VALID,
                AggregationEligibility.INCLUDE, "bad", "bad", None,
            )

    def test_inapplicable_metric_cannot_be_valid(self):
        with self.assertRaises(ValueError):
            MetricContractV1(
                "metric", True, MetricApplicability.NOT_EVALUABLE, MetricValidity.VALID,
                AggregationEligibility.EXCLUDE_UNDEFINED_ONLY, "bad", "missing", None,
            )

    def test_inapplicable_metric_cannot_be_aggregated(self):
        with self.assertRaises(ValueError):
            MetricContractV1(
                "metric", True, MetricApplicability.NOT_EVALUABLE, MetricValidity.NOT_EVALUABLE,
                AggregationEligibility.INCLUDE, "bad", "missing", None,
            )

    def test_missing_legacy_value_becomes_not_evaluable_not_zero(self):
        migrated = migrate_metric_record({"metric_id": "metric.r2", "value": None, "undefined_reason": "constant_target"})
        self.assertIsNone(migrated["original_value"])
        self.assertEqual(migrated["contract"]["applicability"], "NOT_EVALUABLE")

    def test_present_legacy_value_is_preserved_without_new_validity_authority(self):
        migrated = migrate_metric_record({"metric_id": "metric.mae", "value": 3.25})
        self.assertEqual(migrated["original_value"], 3.25)
        self.assertEqual(migrated["contract"]["validity"], "NOT_RECORDED")


class CandidateValidityTests(unittest.TestCase):
    def test_warning_is_representable_without_automatic_rejection(self):
        record = CandidateValidityV1(
            "SUCCESS", True, OptimizerStatus.WARNING, ("MAX_ITER",), GateState.WARN, "adapter.policy.v1"
        )
        self.assertEqual(record.adapter_validity_state, GateState.WARN)

    def test_missing_optimizer_provenance_cannot_be_pass(self):
        with self.assertRaises(ValueError):
            CandidateValidityV1("SUCCESS", True, OptimizerStatus.NOT_REPORTED, (), GateState.PASS, "bad")

    def test_optimizer_failure_cannot_be_pass(self):
        with self.assertRaises(ValueError):
            CandidateValidityV1("FAILED", False, OptimizerStatus.FAILED, (), GateState.PASS, "bad")

    def test_legacy_missing_optimizer_maps_to_not_evaluable(self):
        migrated = migrate_candidate_validity({"finite_output": True})
        self.assertEqual(migrated.optimizer_status, OptimizerStatus.NOT_REPORTED)
        self.assertEqual(migrated.adapter_validity_state, GateState.NOT_EVALUABLE)

    def test_explicit_warning_maps_to_warn(self):
        migrated = migrate_candidate_validity({"finite_output": True, "fit_status": "SUCCESS", "optimizer_status": "WARNING"})
        self.assertEqual(migrated.adapter_validity_state, GateState.WARN)


if __name__ == "__main__":
    unittest.main()

