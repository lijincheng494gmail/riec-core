# v0.9 compatibility

The compatibility layer is additive and interpretive. It preserves scientific values, canonical decisions, gate states, primary events, actions, and evidence authority.

- Unknown legacy metadata maps to `NOT_RECORDED` or `NOT_EVALUABLE`, never fabricated `PASS`.
- `SELECT_WITH_CONDITIONS` normalizes to base action `SELECT` plus qualification and round-trips exactly.
- Undefined metrics are not converted to zero.
- Finite output does not imply optimizer convergence.
- Historical constraint events remain immutable primary events.
- Legacy migration adapters never silently acquire a development lifecycle.

Rollback selects the immutable canonical v0.9 consumer path. It does not rewrite or delete either artifact.
