"""Compatibility-only migration. Scientific values and decisions are never recomputed."""

from __future__ import annotations

from typing import Any, Mapping

from adapters.base import AdapterLifecycle, LifecycleEvidence, validate_lifecycle_transition
from riec_core.models import GateState
from riec_core.v1_contracts import (
    ActionEnvelopeV1,
    AggregationEligibility,
    CandidateValidityV1,
    ConstraintResultV1,
    MetricApplicability,
    MetricContractV1,
    MetricValidity,
    OptimizerStatus,
)


def migrate_action(action: str, *, conditions: tuple[str, ...] = ()) -> ActionEnvelopeV1:
    return ActionEnvelopeV1.from_legacy(action, conditions=conditions)


def migrate_metric_record(record: Mapping[str, Any]) -> dict[str, Any]:
    metric_id = str(record.get("metric_id") or record.get("metric_or_loss_id") or "LEGACY.UNKNOWN_METRIC")
    value_present = "value" in record and record["value"] is not None
    if not value_present:
        contract = MetricContractV1(
            metric_or_loss_id=metric_id,
            metric_exists=True if metric_id != "LEGACY.UNKNOWN_METRIC" else None,
            applicability=MetricApplicability.NOT_EVALUABLE,
            validity=MetricValidity.NOT_EVALUABLE,
            aggregation_eligibility=AggregationEligibility.EXCLUDE_UNDEFINED_ONLY,
            aggregation_rule="exclude_undefined_metric_only_retain_case",
            undefined_handling=str(record.get("undefined_reason") or "LEGACY_NOT_RECORDED"),
        )
    else:
        contract = MetricContractV1(
            metric_or_loss_id=metric_id,
            metric_exists=True,
            applicability=MetricApplicability.NOT_RECORDED,
            validity=MetricValidity.NOT_RECORDED,
            aggregation_eligibility=AggregationEligibility.NOT_RECORDED,
            aggregation_rule="legacy_value_preserved_no_new_aggregation_authority",
            undefined_handling="NOT_APPLICABLE_VALUE_PRESENT",
        )
    return {"original_value": record.get("value"), "contract": contract.to_dict()}


def migrate_candidate_validity(record: Mapping[str, Any]) -> CandidateValidityV1:
    status_text = str(record.get("optimizer_status") or "NOT_REPORTED")
    optimizer_status = OptimizerStatus(status_text)
    finite_output = record.get("finite_output")
    if finite_output not in {True, False, None}:
        raise ValueError("finite_output must be boolean or null")
    if optimizer_status is OptimizerStatus.CONVERGED:
        adapter_state = GateState.PASS
    elif optimizer_status is OptimizerStatus.WARNING:
        adapter_state = GateState.WARN
    elif optimizer_status is OptimizerStatus.FAILED:
        adapter_state = GateState.FAIL
    elif optimizer_status is OptimizerStatus.NOT_APPLICABLE:
        adapter_state = GateState.PASS
    else:
        adapter_state = GateState.NOT_EVALUABLE
    return CandidateValidityV1(
        fit_status=str(record.get("fit_status") or "NOT_RECORDED"),
        finite_output=finite_output,
        optimizer_status=optimizer_status,
        warning_codes=tuple(record.get("warning_codes") or ()),
        adapter_validity_state=adapter_state,
        adapter_policy_id=str(record.get("adapter_policy_id") or "LEGACY.NOT_RECORDED"),
        notes=("compatibility_annotation_only",),
    )


def migrate_constraint_event(
    primary_event: str | None,
    *,
    source_hash: str,
    sealed_conditions: tuple[str, ...] = (),
) -> ConstraintResultV1:
    return ConstraintResultV1(
        primary_event=primary_event,
        conditions=sealed_conditions,
        primary_event_source_hash=source_hash,
        legacy_event_preserved=True,
    )


def migrate_lifecycle(
    current: str,
    *,
    requested: str | None = None,
    evidence: LifecycleEvidence | None = None,
) -> AdapterLifecycle:
    current_state = AdapterLifecycle(current)
    requested_state = AdapterLifecycle(requested or current)
    if current_state != requested_state:
        if evidence is None:
            raise ValueError("a lifecycle transition requires explicit evidence")
        validate_lifecycle_transition(current_state, requested_state, evidence)
    return requested_state

