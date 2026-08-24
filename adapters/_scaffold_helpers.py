"""Construction helpers confined to the adapter layer."""

from riec_core.models import ScientificStatus
from riec_core.protocol import SupportDefinition, TargetIdentity, UnitDeclaration


def placeholder_target(adapter_id: str, status: ScientificStatus) -> TargetIdentity:
    return TargetIdentity(
        version="0.1.0",
        target_id=f"{adapter_id}:mapping_only",
        target_kind="unresolved_mapping",
        unit=None,
        scale="UNDEFINED",
        support=SupportDefinition("0.1.0", "UNDEFINED", "mapping only", "no empirical execution"),
        horizon=None,
        feature_context_id=None,
        allowed_claims=("schema_mapping_only",),
        prohibited_claims=("scientific_result", "operational_recommendation"),
        scientific_status=status,
    )


def placeholder_units(adapter_id: str, status: ScientificStatus) -> tuple[UnitDeclaration, UnitDeclaration]:
    reason = f"{adapter_id.upper()}.UNIT_NOT_MATERIALIZED"
    return (
        UnitDeclaration("0.1.0", "UNDEFINED", (), (), "flat", True, (reason,)),
        UnitDeclaration("0.1.0", "UNDEFINED", (), (), "flat", True, (reason,)),
    )
