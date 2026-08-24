from adapters._scaffold_helpers import placeholder_target, placeholder_units
from adapters.base import AdapterDescriptor, AdapterLifecycle, MappingScaffoldAdapter
from riec_core.models import ArtifactOrigin, ScientificStatus, TaskFamily
from riec_core.quarantine import QuarantineCatalog


class EcoMigrationAdapter(MappingScaffoldAdapter):
    def __init__(self, catalog: QuarantineCatalog) -> None:
        records = catalog.by_project("ECO")
        descriptor = AdapterDescriptor(
            adapter_id="eco",
            adapter_version="0.1.0-scaffold",
            task_family=TaskFamily.EVIDENCE_SYNTHESIS,
            lifecycle=AdapterLifecycle.MIGRATION_SCAFFOLD,
            origin=ArtifactOrigin.NEW_ARCHITECTURE_PROPOSAL,
            discrepancy_ids=tuple(record.discrepancy_id for record in records),
            limitations=(
                "historical invalid YAML remains unmodified and quarantined",
                "Fig4 metric-key conflict is blocked from migration",
                "semantic transfer and primary ablation failures remain limitations",
                "no Benchmark V3 execution occurs",
            ),
        )
        super().__init__(descriptor, placeholder_target("eco", ScientificStatus.REQUIRES_RECONCILIATION), placeholder_units("eco", ScientificStatus.MIGRATION_SCAFFOLD), records)
