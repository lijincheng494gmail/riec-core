from dataclasses import replace
from datetime import datetime, timezone
import json
from pathlib import Path

from riec_core.canonical import canonical_checksum
from riec_core.engines.predictive import CandidateEvaluation, RiskRecord
from riec_core.gates import GateResult
from riec_core.models import (
    ArtifactOrigin,
    EvidenceAuthority,
    GateState,
    Repairability,
    TaskFamily,
    WeightingMode,
)
from riec_core.protocol import DecisionWeighting, MethodSpec, Protocol, TranslationRule


ROOT = Path(__file__).resolve().parents[2]
FIXED_TIME = datetime(2026, 1, 1, tzinfo=timezone.utc)


def load_predictive_protocol() -> Protocol:
    payload = json.loads((ROOT / "examples" / "minimal_predictive_protocol.json").read_text(encoding="utf-8"))
    return Protocol.from_dict(payload)


def load_synthesis_protocol() -> Protocol:
    protocol = load_predictive_protocol()
    return replace(
        protocol,
        protocol_id="synthetic.synthesis.minimum",
        task_family=TaskFamily.EVIDENCE_SYNTHESIS,
        method=MethodSpec(
            "0.1.0", "synthesis_protocol_graph", "synthetic-evidence-graph", ("synthetic-estimator",), ()
        ),
        decision_weighting=DecisionWeighting(
            "0.1.0", WeightingMode.EVIDENCE_WEIGHTING, "synthetic-weighting-v1", ("variance",)
        ),
        translation_rule=TranslationRule(
            "0.1.0", "0.1.0", "synthetic-synthesis-translation", "SYNTHETIC",
            ("RESOLVE", "STRATIFY", "DOWNGRADE", "ABSTAIN"),
        ),
    )


def make_gate(
    state: GateState,
    *,
    gate_id: str = "G0",
    affected_actions: tuple[str, ...] = ("*",),
    permitted_actions: tuple[str, ...] = (),
    conditions: tuple[str, ...] = (),
) -> GateResult:
    if state is GateState.WARN:
        permitted_actions = permitted_actions or ("SELECT", "RESOLVE")
        conditions = conditions or ("synthetic_condition",)
    return GateResult(
        gate_id=gate_id,
        gate_version="0.1.0",
        state=state,
        reason_code=f"SYNTHETIC.{gate_id}.{state.value}",
        evidence_refs=(f"fixture:{gate_id}",),
        affected_actions=affected_actions,
        repairability=Repairability.EVIDENCE_ACQUIRABLE,
        timestamp=FIXED_TIME,
        config_hash=canonical_checksum({"gate": gate_id, "state": state.value}),
        permitted_actions=permitted_actions,
        conditions=conditions,
        origin=ArtifactOrigin.RUNTIME_RESULT,
    )


def pass_gates() -> tuple[GateResult, ...]:
    return tuple(make_gate(GateState.PASS, gate_id=f"G{i}") for i in range(7))


def candidate(
    candidate_id: str,
    risk: float,
    *,
    complexity: float = 1.0,
    burden: float = 1.0,
    stability: float | None = 0.9,
    eligible: bool = True,
    authority: EvidenceAuthority = EvidenceAuthority.FORMAL,
) -> CandidateEvaluation:
    return CandidateEvaluation(
        candidate_id=candidate_id,
        candidate_version="0.1.0",
        risk=RiskRecord("synthetic-risk", "0.1.0", risk, 0.01, "unit", "synthetic", 4, "group"),
        worst_unit_metrics=(("worst", risk + 0.1),),
        stability=stability,
        complexity=complexity,
        deployment_burden=burden,
        eligible=eligible,
        authority=authority,
        reason_codes=("SYNTHETIC.CANDIDATE",),
    )
