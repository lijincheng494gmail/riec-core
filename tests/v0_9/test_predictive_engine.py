import unittest

from riec_core.engines.predictive import (
    AbsoluteTolerancePolicy,
    DecisionOrder,
    NearOptimalPolicy,
    NearOptimalSet,
    PredictiveEngine,
    StableIdFallbackPolicy,
)
from riec_core.models import EvidenceAuthority, GateState, PredictiveAction

from helpers import FIXED_TIME, candidate, load_predictive_protocol, make_gate, pass_gates


class EmptyPolicy(NearOptimalPolicy):
    policy_id = "empty-policy"
    policy_version = "0.1.0"

    def form(self, candidates):
        return NearOptimalSet(self.policy_id, self.policy_version, None, (), "synthetic-empty")


class PredictiveEngineTests(unittest.TestCase):
    def setUp(self):
        self.protocol = load_predictive_protocol()
        self.order = DecisionOrder("synthetic-order", "0.1.0", ("complexity", "worst_unit", "deployment_burden"))

    def test_near_optimal_policy_is_configurable(self):
        candidates = (candidate("a", 1.0), candidate("b", 1.15))
        narrow = AbsoluteTolerancePolicy(0.1).form(candidates)
        wide = AbsoluteTolerancePolicy(0.2).form(candidates)
        self.assertEqual(narrow.member_ids, ("a",))
        self.assertEqual(wide.member_ids, ("a", "b"))

    def test_near_optimality_not_equivalence(self):
        result = AbsoluteTolerancePolicy(0.2).form((candidate("a", 1.0), candidate("b", 1.1)))
        self.assertIn("not_statistical_equivalence", result.interpretation)

    def test_preference_selects_with_stable_order(self):
        result = PredictiveEngine.decide(
            self.protocol,
            (candidate("b", 1.0, complexity=1), candidate("a", 1.0, complexity=1)),
            pass_gates(),
            AbsoluteTolerancePolicy(0.0),
            self.order,
            timestamp=FIXED_TIME,
        )
        self.assertEqual(result.action_record.action, PredictiveAction.SELECT)
        self.assertEqual(result.action_record.context.selected_object_ids, ("a",))

    def test_diagnostic_candidate_has_no_decision_authority(self):
        result = PredictiveEngine.decide(
            self.protocol,
            (candidate("diagnostic", 0.1, authority=EvidenceAuthority.DIAGNOSTIC_ONLY), candidate("formal", 1.0)),
            pass_gates(), AbsoluteTolerancePolicy(0.0), self.order, timestamp=FIXED_TIME,
        )
        self.assertEqual(result.action_record.context.selected_object_ids, ("formal",))
        self.assertNotIn("diagnostic", result.provenance.eligible_candidate_ids)

    def test_hard_gate_failure_abstains(self):
        gates = pass_gates() + (make_gate(GateState.FAIL, gate_id="G6"),)
        result = PredictiveEngine.decide(
            self.protocol, (candidate("a", 1.0),), gates, AbsoluteTolerancePolicy(0.0), self.order, timestamp=FIXED_TIME
        )
        self.assertEqual(result.action_record.action, PredictiveAction.ABSTAIN)

    def test_warn_produces_conditional_select(self):
        warning = make_gate(GateState.WARN, gate_id="G6", permitted_actions=("SELECT",), conditions=("monitor",))
        result = PredictiveEngine.decide(
            self.protocol, (candidate("a", 1.0),), (warning,), AbsoluteTolerancePolicy(0.0), self.order, timestamp=FIXED_TIME
        )
        self.assertEqual(result.action_record.action, PredictiveAction.SELECT_WITH_CONDITIONS)
        self.assertEqual(result.action_record.context.conditions, ("monitor",))

    def test_fallback_is_distinct_from_abstention(self):
        result = PredictiveEngine.decide(
            self.protocol,
            (candidate("b", 1.0), candidate("a", 2.0)),
            pass_gates(),
            EmptyPolicy(),
            self.order,
            fallback_policy=StableIdFallbackPolicy(),
            timestamp=FIXED_TIME,
        )
        self.assertEqual(result.action_record.action, PredictiveAction.FALLBACK_SELECT)
        self.assertEqual(result.action_record.context.selected_object_ids, ("a",))

    def test_empty_eligibility_abstains(self):
        result = PredictiveEngine.decide(
            self.protocol,
            (candidate("a", 1.0, eligible=False),),
            pass_gates(), AbsoluteTolerancePolicy(0.0), self.order, timestamp=FIXED_TIME,
        )
        self.assertEqual(result.action_record.action, PredictiveAction.ABSTAIN)

    def test_no_historical_one_se_default(self):
        self.assertFalse(hasattr(PredictiveEngine, "ONE_SE_THRESHOLD"))


if __name__ == "__main__":
    unittest.main()
