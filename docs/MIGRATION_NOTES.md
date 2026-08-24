# Migration notes

Target: `1.0.0-rc.2` with status `RELEASE_CANDIDATE_NOT_FROZEN`. The original plan targeted rc.1; the number advanced after the logged implementation-test correction, as required by release policy.

Consumers may continue reading v0.9 records. For v1-aware consumers, add release identity, metric applicability/validity, optimizer provenance, two-layer constraint metadata, action qualification, threshold ownership, audit lineage, and the accepted boundary hash. Do not populate absent evidence by inference.

The RC does not require data migration, retraining, prediction regeneration, scientific recomputation, or amendment of historical results.
