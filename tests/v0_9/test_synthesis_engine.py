import unittest

from riec_core.engines.synthesis import (
    ClaimWorld,
    EvidenceNode,
    InsufficientSupportPolicy,
    SynthesisEngine,
    WeightingRoute,
)
from riec_core.models import GateState, SynthesisAction, UncertaintySource

from helpers import FIXED_TIME, load_synthesis_protocol, make_gate, pass_gates


def world(identifier):
    return ClaimWorld(identifier, "0.1.0", f"target:{identifier}", "estimand", "support", "translation")


def node(identifier, claim_world, uncertainty=UncertaintySource.OBSERVED):
    return EvidenceNode(identifier, f"protocol:{identifier}", claim_world, True, uncertainty, (f"source:{identifier}",))


class SynthesisEngineTests(unittest.TestCase):
    def setUp(self):
        self.protocol = load_synthesis_protocol()

    def decide(self, nodes, **kwargs):
        return SynthesisEngine.decide(
            self.protocol,
            nodes,
            kwargs.pop("gates", pass_gates()),
            weighting_route=kwargs.pop("weighting_route", WeightingRoute.NONE),
            minimum_support=kwargs.pop("minimum_support", 1),
            insufficient_support_policy=kwargs.pop("insufficient_support_policy", InsufficientSupportPolicy.ABSTAIN),
            timestamp=FIXED_TIME,
        )

    def test_same_claim_world_resolves(self):
        w = world("same")
        decision = self.decide((node("a", w), node("b", w)))
        self.assertEqual(decision.action_record.action, SynthesisAction.RESOLVE)
        self.assertEqual(len(decision.partitions), 1)

    def test_two_claim_worlds_stratify(self):
        decision = self.decide((node("a", world("a")), node("b", world("b"))))
        self.assertEqual(decision.action_record.action, SynthesisAction.STRATIFY)
        self.assertEqual(len(decision.partitions), 2)

    def test_stratify_does_not_pool_nodes(self):
        decision = self.decide((node("a", world("a")), node("b", world("b"))))
        self.assertTrue(all(selected.startswith("partition:") for selected in decision.action_record.context.selected_object_ids))

    def test_insufficient_support_can_abstain(self):
        decision = self.decide((node("a", world("a")),), minimum_support=2)
        self.assertEqual(decision.action_record.action, SynthesisAction.ABSTAIN)

    def test_insufficient_support_can_downgrade_claim(self):
        decision = self.decide(
            (node("a", world("a")),),
            minimum_support=2,
            insufficient_support_policy=InsufficientSupportPolicy.DOWNGRADE,
        )
        self.assertEqual(decision.action_record.action, SynthesisAction.DOWNGRADE)
        self.assertEqual(decision.action_record.context.claim_scope, "audit_only")

    def test_unknown_variance_blocks_inverse_variance_route(self):
        decision = self.decide(
            (node("a", world("a"), UncertaintySource.UNAVAILABLE),),
            weighting_route=WeightingRoute.INVERSE_VARIANCE,
        )
        self.assertEqual(decision.action_record.action, SynthesisAction.DOWNGRADE)
        self.assertEqual(decision.action_record.context.claim_scope, "unweighted_audit_only")

    def test_hard_gate_failure_abstains(self):
        decision = self.decide(
            (node("a", world("a")),), gates=(make_gate(GateState.FAIL, gate_id="G1"),)
        )
        self.assertEqual(decision.action_record.action, SynthesisAction.ABSTAIN)

    def test_no_eligible_nodes_abstains(self):
        w = world("a")
        ineligible = EvidenceNode("a", "p", w, False, UncertaintySource.OBSERVED, ("source",))
        self.assertEqual(self.decide((ineligible,)).action_record.action, SynthesisAction.ABSTAIN)


if __name__ == "__main__":
    unittest.main()
