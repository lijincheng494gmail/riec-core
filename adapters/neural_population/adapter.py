from adapters._scaffold_helpers import placeholder_target, placeholder_units
from adapters.base import AdapterDescriptor, AdapterLifecycle, LockboxClosedError, MappingScaffoldAdapter
from riec_core.models import ArtifactOrigin, ScientificStatus, TaskFamily


class NeuralPopulationPlaceholderAdapter(MappingScaffoldAdapter):
    def __init__(self) -> None:
        descriptor = AdapterDescriptor(
            adapter_id="neural_population",
            adapter_version="0.1.0-lockbox-placeholder",
            task_family=TaskFamily.PREDICTIVE_SELECTION,
            lifecycle=AdapterLifecycle.LOCKBOX_NOT_OPENED,
            origin=ArtifactOrigin.NEW_ARCHITECTURE_PROPOSAL,
            discrepancy_ids=(),
            limitations=(
                "STATUS=LOCKBOX_NOT_OPENED",
                "no data or oracle access",
                "no post-freeze configuration is accepted",
            ),
        )
        super().__init__(descriptor, placeholder_target("neural_population", ScientificStatus.LOCKBOX_NOT_OPENED), placeholder_units("neural_population", ScientificStatus.LOCKBOX_NOT_OPENED), ())

    def run_candidates(self):
        raise LockboxClosedError("neural_population lockbox is not opened")

    def build_evidence_graph(self):
        raise LockboxClosedError("neural_population lockbox is not opened")
