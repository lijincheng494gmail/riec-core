import unittest
from dataclasses import replace

from riec_core.gates import GateEngine
from riec_core.models import EligibilityState, GateState, ScientificStatus, UncertaintySource
from riec_core.protocol import SupportDefinition, TargetIdentity, UnitDeclaration, UncertaintyProvenance
from riec_core.validation import (
    deployment_defined_gate,
    leakage_sentinel,
    target_compatibility_gate,
    uncertainty_route_gate,
)

from helpers import FIXED_TIME, load_predictive_protocol, make_gate, pass_gates


class SyntheticContractTests(unittest.TestCase):
    def test_different_targets_fail_compatibility(self):
        target = load_predictive_protocol().target
        other = replace(target, target_id="different-target")
        gate = target_compatibility_gate(target, other, timestamp=FIXED_TIME)
        self.assertEqual(gate.state, GateState.FAIL)

    def test_same_target_passes_compatibility(self):
        target = load_predictive_protocol().target
        self.assertEqual(target_compatibility_gate(target, target, timestamp=FIXED_TIME).state, GateState.PASS)

    def test_undefined_deployment_is_not_evaluable(self):
        unit = UnitDeclaration("0.1.0", "UNDEFINED", (), (), "flat", True, ("UNIT.UNKNOWN",))
        gate = deployment_defined_gate(unit, timestamp=FIXED_TIME)
        self.assertEqual(gate.state, GateState.NOT_EVALUABLE)
        self.assertEqual(GateEngine.evaluate((gate,), "SELECT").eligibility, EligibilityState.NOT_EVALUABLE)

    def test_synthetic_leakage_is_detected(self):
        gate = leakage_sentinel(("g1", "g2"), ("g2", "g3"), timestamp=FIXED_TIME)
        self.assertEqual(gate.state, GateState.FAIL)
        self.assertIn("g2", gate.evidence_refs)

    def test_disjoint_units_pass_leakage_sentinel(self):
        gate = leakage_sentinel(("g1",), ("g2",), timestamp=FIXED_TIME)
        self.assertEqual(gate.state, GateState.PASS)

    def test_unknown_variance_is_not_evaluable_for_variance_route(self):
        uncertainty = replace(
            load_predictive_protocol().uncertainty_provenance,
            source_class=UncertaintySource.UNAVAILABLE,
            scientific_status=ScientificStatus.NOT_EVALUABLE,
        )
        gate = uncertainty_route_gate(uncertainty, requires_variance=True, timestamp=FIXED_TIME)
        self.assertEqual(gate.state, GateState.NOT_EVALUABLE)

    def test_one_hard_fail_blocks_claim_grade_eligibility(self):
        gates = list(pass_gates())
        gates[1] = make_gate(GateState.FAIL, gate_id="G1")
        self.assertEqual(GateEngine.evaluate(tuple(gates), "RESOLVE").eligibility, EligibilityState.INELIGIBLE)


if __name__ == "__main__":
    unittest.main()
