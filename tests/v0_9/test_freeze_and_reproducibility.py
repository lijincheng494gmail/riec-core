import unittest

from riec_core.freeze import AmendmentClass, FreezeGuard, FreezeRecord, FreezeState, SubstantiveMutationError
from riec_core.reproducibility import (
    FloatTolerancePolicy,
    StochasticComparisonPolicy,
    compare_exact,
    compare_float,
    compare_stochastic,
)


class FreezeAndReproducibilityTests(unittest.TestCase):
    def test_phase3_freeze_record_is_draft(self):
        record = FreezeRecord.draft("phase3-draft", "0.1.0", {"schema": "0.1.0"})
        self.assertEqual(record.state, FreezeState.DRAFT)
        self.assertFalse(record.oracle_opened)

    def test_semantic_mutation_is_detected(self):
        record = FreezeRecord.draft("phase3-draft", "0.1.0", {"threshold": 1})
        with self.assertRaises(SubstantiveMutationError):
            FreezeGuard.assert_semantic_unchanged(record, {"threshold": 2})

    def test_unchanged_semantics_pass(self):
        payload = {"schema": "0.1.0", "order": ["a", "b"]}
        FreezeGuard.assert_semantic_unchanged(FreezeRecord.draft("draft", "0.1.0", payload), payload)

    def test_outcome_informed_change_is_substantive(self):
        self.assertEqual(
            FreezeGuard.classify_change(semantic_hash_changed=False, outcome_informed=True),
            AmendmentClass.SUBSTANTIVE_CHANGE,
        )

    def test_exact_structural_comparison(self):
        self.assertTrue(compare_exact({"b": 2, "a": 1}, {"a": 1, "b": 2}))

    def test_float_tolerance_requires_decision_invariance(self):
        policy = FloatTolerancePolicy("float", "0.1.0", 1e-6, 1e-6, True)
        self.assertTrue(compare_float(1.0, 1.0000001, policy, left_action="SELECT", right_action="SELECT"))
        self.assertFalse(compare_float(1.0, 1.0000001, policy, left_action="SELECT", right_action="ABSTAIN"))

    def test_stochastic_comparison_requires_seed_identity(self):
        policy = StochasticComparisonPolicy("stochastic", "0.1.0", 0.01, True, True)
        self.assertTrue(compare_stochastic((1.0, 2.0), (1.001, 1.999), (1, 2), (1, 2), policy, left_action="SELECT", right_action="SELECT"))
        self.assertFalse(compare_stochastic((1.0, 2.0), (1.001, 1.999), (1, 2), (2, 1), policy, left_action="SELECT", right_action="SELECT"))


if __name__ == "__main__":
    unittest.main()
