# Public projection record

Projection date: 24 August 2026.

This GitHub repository was derived from the immutable local `RIEC_CORE_V1_0_FROZEN` directory. The scientific/runtime source payload was retained, but the public repository is not itself the authoritative final seal.

## Deliberate projection changes

1. Machine-local absolute paths in the inheritance policy, historical replay helper and rollback guide were replaced with portable caller-supplied references.
2. The final package's self-referential manifest/checksum/provenance files were not copied because removing paths and adding public documentation necessarily changes the GitHub tree.
3. GitHub-facing README, citation, license notice, ignore rules and projection documentation were added.
4. Bytecode and cache artifacts were excluded.

The source RC sealing metadata in `release/` is retained as historical provenance, not as a checksum claim for this modified public tree.

No scientific rule, threshold, gate, schema semantic, action ontology, metric applicability or compatibility behavior was intentionally changed by this projection.
