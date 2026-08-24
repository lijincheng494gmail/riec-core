from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / "release"
BOUNDARY_HASH = "0c51a2877d34bb69165d8b77acffe8534836a5c2e54913f780498da17ca909cf"
CANONICAL_LEDGER_HASH = "642715f29d92d27b564a74d267054e0f595bf0162bc39568bff4fda3d4fdc4f1"
CHANGESET_HASH = "c12ddd44a648774dd9f941beb4489d3eaf275c258b0bbd6d82a9a646898a3142"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ReleaseIntegrationTests(unittest.TestCase):
    def test_public_version_and_status_are_rc_only(self) -> None:
        init_text = (ROOT / "src/riec_core/__init__.py").read_text(encoding="utf-8")
        manifest = (RELEASE / "RIEC_CORE_V1_0_RC_MANIFEST.yaml").read_text(encoding="utf-8")
        self.assertIn('__version__ = "1.0.0-rc.2"', init_text)
        self.assertIn("release_status: RELEASE_CANDIDATE_NOT_FROZEN", manifest)
        self.assertIn("core_v1_frozen: false", manifest)

    def test_manifest_binds_authoritative_hashes(self) -> None:
        manifest = (RELEASE / "RIEC_CORE_V1_0_RC_MANIFEST.yaml").read_text(encoding="utf-8")
        for expected in (BOUNDARY_HASH, CANONICAL_LEDGER_HASH, CHANGESET_HASH):
            self.assertIn(expected, manifest)

    def test_example_binds_boundary_and_retains_negative_results(self) -> None:
        example = json.loads((ROOT / "examples/minimal_v1_rc_envelope.json").read_text())
        self.assertEqual(example["audit"]["post_waiver_boundary_hash"], BOUNDARY_HASH)
        self.assertIs(example["audit"]["negative_results_retained"], True)

    def test_release_file_manifest_is_complete_under_declared_policy(self) -> None:
        manifest_path = RELEASE / "RIEC_CORE_V1_0_RC_FILE_MANIFEST.csv"
        with manifest_path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        observed = {row["relative_path"] for row in rows}
        excluded = {
            "release/RIEC_CORE_V1_0_RC_FILE_MANIFEST.csv",
            "release/RIEC_CORE_V1_0_RC_CHECKSUMS_SHA256.txt",
        }
        expected = {
            path.relative_to(ROOT).as_posix()
            for path in ROOT.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
        } - excluded
        self.assertEqual(observed, expected)
        for row in rows:
            path = ROOT / row["relative_path"]
            self.assertEqual(row["sha256"], digest(path))
            self.assertEqual(int(row["size_bytes"]), path.stat().st_size)

    def test_checksum_ledger_covers_every_file_except_itself(self) -> None:
        ledger_path = RELEASE / "RIEC_CORE_V1_0_RC_CHECKSUMS_SHA256.txt"
        entries = {}
        for line in ledger_path.read_text(encoding="utf-8").splitlines():
            value, relative = line.split("  ", 1)
            entries[relative] = value
        expected = {
            path.relative_to(ROOT).as_posix()
            for path in ROOT.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts and path != ledger_path
        }
        self.assertEqual(set(entries), expected)
        for relative, expected_hash in entries.items():
            self.assertEqual(digest(ROOT / relative), expected_hash)

    def test_claim_boundary_document_is_present(self) -> None:
        text = (ROOT / "docs/CLAIM_BOUNDARY.md").read_text(encoding="utf-8")
        self.assertIn(BOUNDARY_HASH, text)
        self.assertIn("never represented as a completed experiment", text)

    def test_rollback_is_non_destructive(self) -> None:
        text = (ROOT / "docs/ROLLBACK.md").read_text(encoding="utf-8")
        self.assertIn("consumer-pointer", text)
        self.assertIn("No down-migration or destructive rewrite", text)

    def test_package_contains_no_scientific_payload_extensions(self) -> None:
        prohibited = {".npy", ".npz", ".parquet", ".pkl", ".pickle", ".h5", ".hdf5"}
        found = {path.suffix.lower() for path in ROOT.rglob("*") if path.is_file()} & prohibited
        self.assertEqual(found, set())

    def test_only_logged_non_scientific_test_amendment_exists(self) -> None:
        log_path = RELEASE / "implementation_amendment_log.csv"
        with log_path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["change_id"], "V1C-010")
        self.assertEqual(rows[0]["scientific_semantics_changed"], "NO")
        self.assertEqual(rows[1]["amendment_id"], "IA-002")
        self.assertEqual(rows[1]["scientific_semantics_changed"], "NO")

    def test_schema_and_migration_mark_scientific_change_false(self) -> None:
        schema = json.loads(
            (ROOT / "schemas/compatibility/v0_9-to-v1-migration.schema.json").read_text()
        )
        text = json.dumps(schema, sort_keys=True)
        self.assertIn('"scientific_values_changed": {"const": false}', text)


if __name__ == "__main__":
    unittest.main()
