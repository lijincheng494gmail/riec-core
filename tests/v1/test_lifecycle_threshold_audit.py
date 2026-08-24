import unittest

from adapters.base import AdapterLifecycle, LifecycleEvidence, validate_lifecycle_transition
from compatibility.migrate_v0_9 import migrate_lifecycle
from riec_core.v1_contracts import AuditEnvelopeV1, ReleaseIdentityV1, ReleaseStatus, ThresholdOwner, ThresholdRecordV1


HASH = "b" * 64
READY_REFS = ("target", "unit", "protocol", "split", "constraint", "adapter")


class LifecycleTests(unittest.TestCase):
    def test_new_lifecycle_values_exist(self):
        self.assertEqual(AdapterLifecycle.DEVELOPMENT_READY.value, "DEVELOPMENT_READY")
        self.assertEqual(AdapterLifecycle.DEVELOPMENT_VALIDATED.value, "DEVELOPMENT_VALIDATED")

    def test_ready_requires_frozen_inputs_and_smoke_audit(self):
        with self.assertRaises(ValueError):
            validate_lifecycle_transition(
                AdapterLifecycle.NOT_STARTED,
                AdapterLifecycle.DEVELOPMENT_READY,
                LifecycleEvidence((), None, None, None),
            )

    def test_ready_accepts_complete_evidence(self):
        validate_lifecycle_transition(
            AdapterLifecycle.NOT_STARTED,
            AdapterLifecycle.DEVELOPMENT_READY,
            LifecycleEvidence(READY_REFS, "smoke", None, None),
        )

    def test_validated_requires_formal_and_validation_references(self):
        with self.assertRaises(ValueError):
            validate_lifecycle_transition(
                AdapterLifecycle.NOT_STARTED,
                AdapterLifecycle.DEVELOPMENT_VALIDATED,
                LifecycleEvidence(READY_REFS, "smoke", None, None),
            )

    def test_validated_accepts_complete_evidence(self):
        validate_lifecycle_transition(
            AdapterLifecycle.NOT_STARTED,
            AdapterLifecycle.DEVELOPMENT_VALIDATED,
            LifecycleEvidence(READY_REFS, "smoke", "formal", "validation"),
        )

    def test_migration_adapter_cannot_silently_promote(self):
        with self.assertRaises(ValueError):
            migrate_lifecycle(
                "MIGRATION_SCAFFOLD",
                requested="DEVELOPMENT_READY",
                evidence=LifecycleEvidence(READY_REFS, "smoke", None, None),
            )

    def test_unchanged_legacy_lifecycle_roundtrips(self):
        self.assertEqual(migrate_lifecycle("MIGRATION_SCAFFOLD"), AdapterLifecycle.MIGRATION_SCAFFOLD)


class ThresholdAndAuditTests(unittest.TestCase):
    def test_adapter_threshold_is_explicit_and_nonuniversal(self):
        record = ThresholdRecordV1("t", ThresholdOwner.ADAPTER, "adapter_scope", 5.0, "sealed", "bounded", "adapter_owner")
        self.assertFalse(record.universal_across_domains)

    def test_universal_numeric_threshold_is_rejected(self):
        with self.assertRaises(ValueError):
            ThresholdRecordV1("t", ThresholdOwner.ADAPTER, "scope", 5.0, "sealed", "bounded", "owner", True)

    def test_audit_accepts_bounded_claims(self):
        record = AuditEnvelopeV1(
            (("source", HASH),), HASH, True, ("CORE-AMEND-CHEM-001",), HASH,
            ("BOUNDED_TYPED_GOVERNANCE",),
        )
        self.assertTrue(record.negative_results_retained)

    def test_audit_rejects_negative_result_deletion(self):
        with self.assertRaises(ValueError):
            AuditEnvelopeV1((("source", HASH),), HASH, False, (), HASH, ())

    def test_audit_rejects_forbidden_claim(self):
        with self.assertRaises(ValueError):
            AuditEnvelopeV1((("source", HASH),), HASH, True, (), HASH, ("UNIVERSAL_GATE_NECESSITY",))

    def test_release_identity_is_unfrozen_rc(self):
        identity = ReleaseIdentityV1("1.0.0-rc.2", ReleaseStatus.RELEASE_CANDIDATE_NOT_FROZEN, HASH, HASH)
        self.assertEqual(identity.status, ReleaseStatus.RELEASE_CANDIDATE_NOT_FROZEN)

    def test_final_version_string_is_rejected(self):
        with self.assertRaises(ValueError):
            ReleaseIdentityV1("1.0.0", ReleaseStatus.RELEASE_CANDIDATE_NOT_FROZEN, HASH, HASH)


if __name__ == "__main__":
    unittest.main()
