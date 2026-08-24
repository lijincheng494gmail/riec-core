from adapters._scaffold_helpers import placeholder_target, placeholder_units
from adapters.base import AdapterDescriptor, AdapterLifecycle, MappingScaffoldAdapter
from riec_core.models import ArtifactOrigin, ScientificStatus, TaskFamily
from riec_core.quarantine import QuarantineCatalog


class DairyMigrationAdapter(MappingScaffoldAdapter):
    def __init__(self, catalog: QuarantineCatalog) -> None:
        records = catalog.by_project("DAIRY")
        descriptor = AdapterDescriptor(
            adapter_id="dairy",
            adapter_version="0.1.0-scaffold",
            task_family=TaskFamily.PREDICTIVE_SELECTION,
            lifecycle=AdapterLifecycle.MIGRATION_SCAFFOLD,
            origin=ArtifactOrigin.NEW_ARCHITECTURE_PROPOSAL,
            discrepancy_ids=tuple(record.discrepancy_id for record in records),
            limitations=(
                "Protein manuscript count is blocked from migration",
                "RCT zero semantics remain UNRESOLVED_SEMANTICS",
                "historical manuscript decision order is not active",
                "no historical candidate or benchmark is executed",
            ),
        )
        super().__init__(descriptor, placeholder_target("dairy", ScientificStatus.REQUIRES_RECONCILIATION), placeholder_units("dairy", ScientificStatus.MIGRATION_SCAFFOLD), records)
