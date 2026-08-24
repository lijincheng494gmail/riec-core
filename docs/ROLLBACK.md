# Rollback

Rollback is a consumer-pointer operation.

1. Stop RC consumers without deleting the RC package.
2. Point consumers to the separately retained immutable canonical v0.9 root supplied by the operator.
3. Verify canonical checksum ledger SHA-256 `642715f29d92d27b564a74d267054e0f595bf0162bc39568bff4fda3d4fdc4f1` and its 72/72 file checks.
4. Run the unchanged v0.9 tests and confirm 98/98 pass.
5. Record the pointer change and preserve all RC, waiver, FAIL, null, and NOT_EVALUABLE evidence.

No down-migration or destructive rewrite is allowed.
