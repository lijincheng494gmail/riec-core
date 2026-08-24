from adapters._scaffold_helpers import placeholder_target, placeholder_units
from adapters.base import AdapterDescriptor, AdapterLifecycle, MappingScaffoldAdapter
from riec_core.models import ArtifactOrigin, ScientificStatus, TaskFamily
from riec_core.quarantine import QuarantineCatalog


class FactoryMigrationAdapter(MappingScaffoldAdapter):
    def __init__(self, catalog: QuarantineCatalog) -> None:
        records = catalog.by_project("FACTORY")
        descriptor = AdapterDescriptor(
            adapter_id="factory",
            adapter_version="0.1.0-scaffold",
            task_family=TaskFamily.PREDICTIVE_SELECTION,
            lifecycle=AdapterLifecycle.MIGRATION_SCAFFOLD,
            origin=ArtifactOrigin.NEW_ARCHITECTURE_PROPOSAL,
            discrepancy_ids=tuple(record.discrepancy_id for record in records),
            limitations=(
                "historical thresholds are not active Core defaults",
                "no historical candidate or benchmark is executed",
                "real-outcome claim remains prohibited",
            ),
        )
        super().__init__(descriptor, placeholder_target("factory", ScientificStatus.MIGRATION_SCAFFOLD), placeholder_units("factory", ScientificStatus.MIGRATION_SCAFFOLD), records)
