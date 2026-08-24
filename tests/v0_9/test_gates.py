import unittest
from dataclasses import replace

from riec_core.gates import GateEngine, GateResult
from riec_core.models import EligibilityState, GateState

from helpers import make_gate, pass_gates


class GateTests(unittest.TestCase):
    def test_all_pass_is_eligible(self):
        decision = GateEngine.evaluate(pass_gates(), "SELECT")
        self.assertEqual(decision.eligibility, EligibilityState.ELIGIBLE)

    def test_one_fail_cannot_be_compensated_by_six_passes(self):
        gates = list(pass_gates())
        gates[4] = make_gate(GateState.FAIL, gate_id="G4")
        decision = GateEngine.evaluate(tuple(gates), "SELECT")
        self.assertEqual(decision.eligibility, EligibilityState.INELIGIBLE)
        self.assertEqual(decision.blocking_gate_ids, ("G4",))

    def test_fail_precedes_not_evaluable(self):
        gates = (make_gate(GateState.NOT_EVALUABLE, gate_id="G3"), make_gate(GateState.FAIL, gate_id="G6"))
        self.assertEqual(GateEngine.evaluate(gates, "SELECT").eligibility, EligibilityState.INELIGIBLE)

    def test_not_evaluable_is_not_pass(self):
        decision = GateEngine.evaluate((make_gate(GateState.NOT_EVALUABLE, gate_id="G3"),), "SELECT")
        self.assertEqual(decision.eligibility, EligibilityState.NOT_EVALUABLE)

    def test_warn_requires_predeclared_action(self):
        warning = make_gate(GateState.WARN, permitted_actions=("RESOLVE",))
        self.assertEqual(GateEngine.evaluate((warning,), "SELECT").eligibility, EligibilityState.INELIGIBLE)

    def test_warn_can_be_conditionally_eligible(self):
        warning = make_gate(GateState.WARN, permitted_actions=("SELECT",), conditions=("bounded",))
        self.assertEqual(GateEngine.evaluate((warning,), "SELECT").eligibility, EligibilityState.CONDITIONALLY_ELIGIBLE)

    def test_warn_without_conditions_is_rejected(self):
        with self.assertRaises(ValueError):
            replace(make_gate(GateState.PASS), state=GateState.WARN)

    def test_no_relevant_gate_is_not_evaluable(self):
        gate = make_gate(GateState.PASS, affected_actions=("RESOLVE",))
        self.assertEqual(GateEngine.evaluate((gate,), "SELECT").eligibility, EligibilityState.NOT_EVALUABLE)

    def test_no_total_gate_score_api(self):
        self.assertFalse(hasattr(GateEngine, "total_gate_score"))


if __name__ == "__main__":
    unittest.main()
