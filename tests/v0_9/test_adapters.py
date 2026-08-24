import inspect
import unittest

from adapters.base import AdapterLifecycle, DomainAdapter, LockboxClosedError, ScientificExecutionForbidden
from adapters.chemistry import ChemistryPlaceholderAdapter
from adapters.dairy import DairyMigrationAdapter
from adapters.eco import EcoMigrationAdapter
from adapters.factory import FactoryMigrationAdapter
from adapters.neural_population import NeuralPopulationPlaceholderAdapter
from riec_core.models import ArtifactOrigin, ScientificStatus
from riec_core.quarantine import QuarantineCatalog

from helpers import ROOT


class AdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = QuarantineCatalog.load(ROOT / "configs" / "quarantine" / "discrepancies.json")

    def test_migration_adapters_satisfy_contract(self):
        for adapter in (FactoryMigrationAdapter(self.catalog), DairyMigrationAdapter(self.catalog), EcoMigrationAdapter(self.catalog)):
            self.assertIsInstance(adapter, DomainAdapter)
            self.assertFalse(inspect.isabstract(adapter.__class__))
            self.assertEqual(adapter.descriptor.lifecycle, AdapterLifecycle.MIGRATION_SCAFFOLD)

    def test_factory_scaffold_cannot_execute(self):
        with self.assertRaises(ScientificExecutionForbidden):
            FactoryMigrationAdapter(self.catalog).run_candidates()

    def test_dairy_scaffold_carries_high_critical_ids(self):
        adapter = DairyMigrationAdapter(self.catalog)
        self.assertIn("D-D004", adapter.descriptor.discrepancy_ids)
        self.assertIn("D-D012", adapter.descriptor.discrepancy_ids)
        self.assertEqual(adapter.describe_target().scientific_status, ScientificStatus.REQUIRES_RECONCILIATION)

    def test_eco_scaffold_carries_metric_key_conflict(self):
        adapter = EcoMigrationAdapter(self.catalog)
        self.assertIn("E-D007", adapter.descriptor.discrepancy_ids)
        self.assertTrue(any("Benchmark V3" in item for item in adapter.descriptor.limitations))

    def test_chemistry_is_not_started(self):
        adapter = ChemistryPlaceholderAdapter()
        self.assertEqual(adapter.descriptor.lifecycle, AdapterLifecycle.NOT_STARTED)
        self.assertEqual(adapter.describe_target().scientific_status, ScientificStatus.NOT_STARTED)
        self.assertEqual(adapter.register_protocols(), ())

    def test_neural_lockbox_is_not_opened(self):
        adapter = NeuralPopulationPlaceholderAdapter()
        self.assertEqual(adapter.descriptor.lifecycle, AdapterLifecycle.LOCKBOX_NOT_OPENED)
        with self.assertRaises(LockboxClosedError):
            adapter.run_candidates()

    def test_adapter_descriptors_are_new_proposals(self):
        adapters = [
            FactoryMigrationAdapter(self.catalog), DairyMigrationAdapter(self.catalog), EcoMigrationAdapter(self.catalog),
            ChemistryPlaceholderAdapter(), NeuralPopulationPlaceholderAdapter(),
        ]
        self.assertTrue(all(adapter.descriptor.origin is ArtifactOrigin.NEW_ARCHITECTURE_PROPOSAL for adapter in adapters))

    def test_mapping_splits_are_not_materialized(self):
        adapter = FactoryMigrationAdapter(self.catalog)
        self.assertEqual(adapter.build_splits().status, ScientificStatus.NOT_STARTED)
        self.assertEqual(adapter.build_splits().membership_refs, ())


if __name__ == "__main__":
    unittest.main()
