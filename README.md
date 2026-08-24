# RIEC-Core v1.0

Public inspection and reproducibility projection of the frozen **RIEC-Core v1.0** protocol-to-claim governance architecture.

RIEC-Core addresses analytical multiplicity: one research question can admit many reasonable inclusion, preprocessing, split, model, metric and synthesis choices. The architecture separates protocol identity, evidence qualification, non-compensatory gates, bounded actions and claim authority so that attractive numerical performance cannot compensate for leakage, duplicated evidence, estimand mismatch or unsupported deployment.

The accompanying preprint is:

> Jincheng Li. **RIEC-Core: Auditing Analytic Multiplicity and Governing Scientific Claims Across Heterogeneous Research Protocols.** SSRN. https://doi.org/10.2139/ssrn.7264499

## Frozen status

- final identity: `RIEC-Core v1.0`;
- source release candidate: `1.0.0-rc.2`;
- frozen at `2026-08-09T17:25:52Z`;
- RC-to-final scientific/runtime content change: **none**;
- development boundary: `CLOSED_AT_V1_0`;
- original RC 81-file tree SHA-256: `937ab4dac2b9b2ba71258e9399ba89cc607c556c5b08fc83c68e4d9786bf94b3`;
- accepted post-waiver claim-boundary SHA-256: `0c51a2877d34bb69165d8b77acffe8534836a5c2e54913f780498da17ca909cf`.

The rc.2 identity remains in source metadata because final promotion was a governance freeze, not a new scientific analysis.

## Architecture

- `src/riec_core/` — typed protocols, evidence records, gates, actions, registries, provenance and audit bundles;
- `schemas/` — machine-readable protocol, gate, action and audit contracts;
- `adapters/` — bounded domain adapters;
- `compatibility/` — v0.9-to-v1 compatibility and optional historical replay;
- `configs/` — configuration, metric applicability and inheritance quarantine;
- `tests/` — v0.9 compatibility and v1 contract tests;
- `release/` — source RC release notes and sealing metadata;
- `docs/` — claim boundary, development closure, rollback and public-projection notes.

## Test

Python 3.12 or later:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
PYTHONPATH=tests/v0_9 python -m unittest discover -s tests
```

`compatibility/replay_historical.py` is an optional read-only replay and requires the caller to supply separately retained Phase 5 and Chemistry artifacts. Those historical payloads are not duplicated in this compact public repository.

## Scientific boundary

Factory, Dairy, Eco and Chemistry were allowed to influence the architecture and are therefore development evidence, not post-freeze external validation. The accepted FB-008 scope waiver excludes component-level necessity/effectiveness, route-by-route necessity/redundancy, complete matched activation coverage, universal gate/threshold superiority and causal or external-benefit claims. Negative, FAIL, null, incomplete and `NOT_EVALUABLE` records remain part of the history.

Later Neuro or other external results may motivate a separately governed v1.1 cycle; they may not be written back into v1.0. See [`docs/CLAIM_BOUNDARY.md`](docs/CLAIM_BOUNDARY.md) and [`RIEC_CORE_V1_0_DEVELOPMENT_BOUNDARY.md`](RIEC_CORE_V1_0_DEVELOPMENT_BOUNDARY.md).

## Public projection versus authoritative freeze

This GitHub projection removes machine-local paths and omits the self-referential whole-package ledger. It therefore does not claim byte identity with the immutable local freeze. All portable changes are enumerated in [`docs/PUBLIC_PROJECTION.md`](docs/PUBLIC_PROJECTION.md), while upstream identities are retained in [`docs/UPSTREAM_FREEZE_IDENTITY.md`](docs/UPSTREAM_FREEZE_IDENTITY.md).

No explicit open-source license was present in the frozen package; see [`LICENSE_NOTICE.md`](LICENSE_NOTICE.md).
