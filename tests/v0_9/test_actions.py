import unittest
from dataclasses import replace

from riec_core.actions import ActionContext, PredictiveActionRecord, SynthesisActionRecord
from riec_core.canonical import canonical_checksum
from riec_core.models import ActionFamily, PredictiveAction, SynthesisAction

from helpers import FIXED_TIME, load_predictive_protocol


def context(*, selected=(), claim_scope=None, conditions=()):
    protocol = load_predictive_protocol()
    return ActionContext(
        action_id="synthetic-action",
        protocol_checksum=protocol.checksum(),
        gate_snapshot_hash=canonical_checksum(()),
        policy_version="0.1.0",
        reason_codes=("SYNTHETIC.REASON",),
        conditions=conditions,
        selected_object_ids=selected,
        claim_scope=claim_scope,
        timestamp=FIXED_TIME,
    )


class ActionTests(unittest.TestCase):
    def test_predictive_select_is_commit(self):
        record = PredictiveActionRecord(context(selected=("candidate-a",)), PredictiveAction.SELECT, ActionFamily.COMMIT)
        self.assertEqual(record.action, PredictiveAction.SELECT)

    def test_select_is_not_resolve(self):
        self.assertNotEqual(PredictiveAction.SELECT.value, SynthesisAction.RESOLVE.value)

    def test_stratify_is_partition_not_multi_select(self):
        record = SynthesisActionRecord(
            context(selected=("partition-a", "partition-b"), claim_scope="partition-specific"),
            SynthesisAction.STRATIFY,
            ActionFamily.PARTITION,
        )
        self.assertEqual(record.family, ActionFamily.PARTITION)

    def test_downgrade_requires_claim_scope(self):
        with self.assertRaises(ValueError):
            SynthesisActionRecord(context(selected=("node",)), SynthesisAction.DOWNGRADE, ActionFamily.BOUND)

    def test_downgrade_is_valid_with_bounded_claim(self):
        record = SynthesisActionRecord(
            context(selected=("node",), claim_scope="audit_only"),
            SynthesisAction.DOWNGRADE,
            ActionFamily.BOUND,
        )
        self.assertEqual(record.context.claim_scope, "audit_only")

    def test_abstain_cannot_select(self):
        with self.assertRaises(ValueError):
            PredictiveActionRecord(context(selected=("candidate",)), PredictiveAction.ABSTAIN, ActionFamily.NON_DECISION)

    def test_conditional_select_requires_conditions(self):
        with self.assertRaises(ValueError):
            PredictiveActionRecord(
                context(selected=("candidate",)), PredictiveAction.SELECT_WITH_CONDITIONS, ActionFamily.BOUND
            )

    def test_wrong_family_is_rejected(self):
        with self.assertRaises(ValueError):
            PredictiveActionRecord(context(selected=("candidate",)), PredictiveAction.SELECT, ActionFamily.BOUND)


if __name__ == "__main__":
    unittest.main()
