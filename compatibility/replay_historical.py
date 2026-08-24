"""Read-only replay of sealed governance summaries; performs no scientific computation."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from compatibility.migrate_v0_9 import migrate_action


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase5-root", type=Path, required=True)
    parser.add_argument("--chemistry-decision", type=Path, required=True)
    args = parser.parse_args()

    matrix_path = args.phase5_root / "11_DECISION_INVARIANCE_MATRIX.csv"
    factory_path = args.phase5_root / "new_core_outputs/factory_representative.json"
    eco_path = args.phase5_root / "new_core_outputs/eco_minimal.json"
    with matrix_path.open(newline="", encoding="utf-8") as handle:
        matrix = list(csv.DictReader(handle))
    factory = json.loads(factory_path.read_text(encoding="utf-8"))
    eco = json.loads(eco_path.read_text(encoding="utf-8"))
    chemistry = json.loads(args.chemistry_decision.read_text(encoding="utf-8"))

    assert len(matrix) == 14
    assert all(row["invariant"] == "YES" for row in matrix)
    comparable = (
        "eligibility",
        "rank",
        "near_optimal",
        "selected",
        "action",
        "claim_boundary",
    )
    assert all(
        row[f"old_{field}"] == row[f"new_{field}"]
        for row in matrix
        for field in comparable
    )
    assert any(row["new_action"] == "FAIL" for row in matrix)
    assert any(row["new_action"] == "NOT_EVALUABLE" for row in matrix)

    assert factory["final_model"] == "GBDT(n=120,lr=0.05,d=3)"
    assert factory["gatekeeper_state"] == "NOT_EVALUABLE_FROM_STORED_SLICE"
    assert factory["fallback_state"] == "FALSE"

    assert eco["semantic_transfer_gate"] == "FAIL"
    assert eco["primary_ablation_gate"] == "FAIL"
    assert eco["fig4_identity_state"] == "DISCREPANCY_PRESERVED"
    assert eco["bounded_cases"]["T9-C04"] == "downgrade"
    assert eco["bounded_cases"]["T9-C05"] == "abstain"

    decision = chemistry["decision"]
    action = decision["action_record"]["action"]
    conditions = tuple(decision["action_record"]["context"]["conditions"])
    migrated = migrate_action(action, conditions=conditions)
    assert chemistry["core_selected_id"] == "P4"
    assert decision["near_optimal_set"]["member_ids"] == ["P4", "P5"]
    assert migrated.base_action == "SELECT"
    assert migrated.to_legacy() == "SELECT_WITH_CONDITIONS"
    assert tuple(migrated.conditions) == conditions
    gates = {record["gate_id"]: record for record in chemistry["gates"]}
    assert gates["G4_CALIBRATION_SUPPORT"]["state"] == "PASS"
    assert gates["G6_PHYSICAL_ADMISSIBILITY"]["state"] == "PASS"

    fields = [
        "replay_id",
        "source_path",
        "source_sha256",
        "records_checked",
        "expected_decision",
        "observed_decision",
        "compatibility_annotation",
        "decision_invariant",
        "negative_or_null_retained",
        "notes",
    ]
    writer = csv.DictWriter(__import__("sys").stdout, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(
        [
            {
                "replay_id": "HR-001",
                "source_path": str(matrix_path),
                "source_sha256": sha256(matrix_path),
                "records_checked": 14,
                "expected_decision": "sealed old_* fields",
                "observed_decision": "all corresponding new_* fields exact",
                "compatibility_annotation": "none; exact sealed comparison",
                "decision_invariant": "YES",
                "negative_or_null_retained": "YES",
                "notes": "Includes Factory, Dairy, Eco, and cross-project fail-closed records.",
            },
            {
                "replay_id": "HR-002",
                "source_path": str(factory_path),
                "source_sha256": sha256(factory_path),
                "records_checked": 3,
                "expected_decision": "GBDT selected; gatekeeper NOT_EVALUABLE; fallback FALSE",
                "observed_decision": "exact",
                "compatibility_annotation": "read-only v1 identity wrapper only",
                "decision_invariant": "YES",
                "negative_or_null_retained": "YES",
                "notes": "No Factory component-level claim is made.",
            },
            {
                "replay_id": "HR-003",
                "source_path": str(eco_path),
                "source_sha256": sha256(eco_path),
                "records_checked": 5,
                "expected_decision": "two FAIL gates; discrepancy/downgrade/abstain retained",
                "observed_decision": "exact",
                "compatibility_annotation": "read-only v1 identity wrapper only",
                "decision_invariant": "YES",
                "negative_or_null_retained": "YES",
                "notes": "No route-by-route necessity or redundancy claim is made.",
            },
            {
                "replay_id": "HR-004",
                "source_path": str(args.chemistry_decision),
                "source_sha256": sha256(args.chemistry_decision),
                "records_checked": 4,
                "expected_decision": "P4; near-optimal P4/P5; SELECT_WITH_CONDITIONS; G4/G6 PASS",
                "observed_decision": "exact; action alias round-trips losslessly",
                "compatibility_annotation": "base_action SELECT + WITH_CONDITIONS",
                "decision_invariant": "YES",
                "negative_or_null_retained": "YES",
                "notes": "Only the sealed decision file is read; no prediction or training is run.",
            },
        ]
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
