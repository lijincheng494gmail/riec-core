from adapters._scaffold_helpers import placeholder_target, placeholder_units
from adapters.base import AdapterDescriptor, AdapterLifecycle, MappingScaffoldAdapter
from riec_core.models import ArtifactOrigin, ScientificStatus, TaskFamily


class ChemistryPlaceholderAdapter(MappingScaffoldAdapter):
    def __init__(self) -> None:
        descriptor = AdapterDescriptor(
            adapter_id="chemistry",
            adapter_version="0.1.0-placeholder",
            task_family=TaskFamily.PREDICTIVE_SELECTION,
            lifecycle=AdapterLifecycle.NOT_STARTED,
            origin=ArtifactOrigin.NEW_ARCHITECTURE_PROPOSAL,
            discrepancy_ids=(),
            limitations=(
                "STATUS=NOT_STARTED",
                "no dataset selected or downloaded",
                "no physical or calibration rule instantiated",
                "no candidate or benchmark executed",
            ),
        )
        super().__init__(descriptor, placeholder_target("chemistry", ScientificStatus.NOT_STARTED), placeholder_units("chemistry", ScientificStatus.NOT_STARTED), ())
