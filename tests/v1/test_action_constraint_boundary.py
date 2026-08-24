import unittest

from compatibility.migrate_v0_9 import migrate_action, migrate_constraint_event
from riec_core.v1_contracts import ActionEnvelopeV1, ActionQualification, ConstraintResultV1, GateSemanticBoundaryV1


HASH = "a" * 64


class ActionEnvelopeTests(unittest.TestCase):
    def test_legacy_conditional_action_normalizes(self):
        action = migrate_action("SELECT_WITH_CONDITIONS", conditions=("bounded",))
        self.assertEqual(action.base_action, "SELECT")
        self.assertEqual(action.qualification, ActionQualification.WITH_CONDITIONS)

    def test_legacy_conditional_action_roundtrips(self):
        action = migrate_action("SELECT_WITH_CONDITIONS", conditions=("bounded",))
        self.assertEqual(action.to_legacy(), "SELECT_WITH_CONDITIONS")

    def test_conditional_action_requires_conditions(self):
        with self.assertRaises(ValueError):
            migrate_action("SELECT_WITH_CONDITIONS")

    def test_unqualified_action_rejects_hidden_conditions(self):
        with self.assertRaises(ValueError):
            ActionEnvelopeV1("ABSTAIN", ActionQualification.NONE, ("hidden",), "ABSTAIN")

    def test_plain_action_roundtrips(self):
        self.assertEqual(migrate_action("DOWNGRADE").to_legacy(), "DOWNGRADE")


class ConstraintTests(unittest.TestCase):
    def test_primary_event_is_preserved_with_overlapping_conditions(self):
        result = migrate_constraint_event("C06", source_hash=HASH, sealed_conditions=("C06", "C07"))
        self.assertEqual(result.primary_event, "C06")
        self.assertEqual(result.conditions, ("C06", "C07"))

    def test_duplicate_conditions_are_rejected(self):
        with self.assertRaises(ValueError):
            ConstraintResultV1("C06", ("C06", "C06"), HASH, True)

    def test_primary_event_rewrite_flag_is_rejected(self):
        with self.assertRaises(ValueError):
            ConstraintResultV1("C06", ("C07",), HASH, False)


class GateBoundaryTests(unittest.TestCase):
    def test_g4_g6_are_distinct_with_conditional_overlap(self):
        boundary = GateSemanticBoundaryV1("G4", "G6", "DISTINCT_WITH_CONDITIONAL_OVERLAP", False)
        self.assertFalse(boundary.merged)

    def test_g4_g6_cannot_be_forced_merged(self):
        with self.assertRaises(ValueError):
            GateSemanticBoundaryV1("G4", "G6", "DISTINCT_WITH_CONDITIONAL_OVERLAP", True)


if __name__ == "__main__":
    unittest.main()

