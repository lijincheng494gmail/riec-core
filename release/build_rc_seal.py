"""Build deterministic release ledgers; does not inspect scientific payloads."""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path


FILE_MANIFEST = "release/RIEC_CORE_V1_0_RC_FILE_MANIFEST.csv"
CHECKSUM_LEDGER = "release/RIEC_CORE_V1_0_RC_CHECKSUMS_SHA256.txt"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def classify(relative: str) -> tuple[str, str, str]:
    if relative == "adapters/base.py":
        return ("CANONICAL_V0_9_PLUS_CHEM001", "CHEM_001", "Lifecycle extension only.")
    if relative in {"src/riec_core/v1_contracts.py", "schemas/v1/riec-core-v1-rc.schema.json"}:
        return ("PHASE8_V1_CANDIDATE", "PHASE8", "Frozen v1 candidate semantics.")
    if relative.startswith("compatibility/") or relative.startswith("schemas/compatibility/"):
        return ("V0_9_TO_V1_COMPATIBILITY", "FB014", "Additive compatibility; no science change.")
    if relative == "tests/v0_9/helpers.py":
        return ("CANONICAL_V0_9_PATH_RELOCATION", "CANONICAL_V0_9", "Root path adjusted for isolated layout.")
    if relative.startswith("tests/v0_9/"):
        return ("CANONICAL_V0_9_UNCHANGED", "CANONICAL_V0_9", "Assertion suite copied unchanged.")
    if relative.startswith("src/riec_core/") and relative != "src/riec_core/__init__.py":
        return ("CANONICAL_V0_9_UNCHANGED", "CANONICAL_V0_9", "Copied from verified v0.9.")
    if relative.startswith(("configs/", "adapters/")):
        return ("CANONICAL_V0_9_UNCHANGED", "CANONICAL_V0_9", "Copied from verified v0.9.")
    if relative.startswith("schemas/") and "/v1/" not in relative and "/compatibility/" not in relative:
        return ("CANONICAL_V0_9_UNCHANGED", "CANONICAL_V0_9", "Copied from verified v0.9.")
    if relative in {"examples/SYNTHETIC_SCENARIOS.md", "examples/minimal_predictive_protocol.json"}:
        return ("CANONICAL_V0_9_UNCHANGED", "CANONICAL_V0_9", "Copied from verified v0.9.")
    if relative.startswith("tests/v1/"):
        return ("V1_RC_VERIFICATION", "FB014", "Tests frozen v1 candidate changes.")
    if relative.startswith("tests/integration/"):
        return ("RC_INTEGRATION_VERIFICATION", "FB014", "Release integrity tests.")
    if relative.startswith("docs/") or relative.startswith("release/"):
        return ("RC_RELEASE_ENGINEERING", "FB014", "Governance and sealing artifact.")
    return ("RC_INTEGRATION", "FB014", "Isolated v1 RC integration artifact.")


def files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--source-provenance", type=Path)
    args = parser.parse_args()
    root = args.package_root.resolve()
    manifest_path = root / FILE_MANIFEST
    checksum_path = root / CHECKSUM_LEDGER

    manifest_rows = []
    for path in files(root):
        relative = path.relative_to(root).as_posix()
        if relative in {FILE_MANIFEST, CHECKSUM_LEDGER}:
            continue
        provenance_class, authority, notes = classify(relative)
        manifest_rows.append(
            {
                "relative_path": relative,
                "sha256": digest(path),
                "size_bytes": path.stat().st_size,
                "provenance_class": provenance_class,
            }
        )
    with manifest_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(manifest_rows[0]))
        writer.writeheader()
        writer.writerows(manifest_rows)

    with checksum_path.open("w", encoding="utf-8", newline="\n") as handle:
        for path in files(root):
            if path == checksum_path:
                continue
            handle.write(f"{digest(path)}  {path.relative_to(root).as_posix()}\n")

    if args.source_provenance:
        rows = []
        for path in files(root):
            relative = path.relative_to(root).as_posix()
            provenance_class, authority, notes = classify(relative)
            rows.append(
                {
                    "relative_path": relative,
                    "sha256": digest(path),
                    "size_bytes": path.stat().st_size,
                    "provenance_class": provenance_class,
                    "source_authority": authority,
                    "notes": notes,
                }
            )
        args.source_provenance.parent.mkdir(parents=True, exist_ok=True)
        with args.source_provenance.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
