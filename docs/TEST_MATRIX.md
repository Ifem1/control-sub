# Verification Matrix

## Offline mocked SDK suite

`tests/test_contract.py` executes the actual Python contract against a minimal test double. It does **not** execute GenVM nor prove real consensus. It covers complete pass, missing dimension, unknown dimension, forged leader, new weakening, source digest mismatch, unavailable/oversize sources, non-allowlisted/moving Git URLs, duplicate source inflation, typoed objective IDs, duplicate IDs, unsupported/unordered/repeated evidence indexes, malformed verdicts, owner-only ratification, stale hashes, stale ratification, replay assessment, supersession, time expiry, revocation, owner rejection, and consumer predicate false on unknown IDs. `tests/test_consumer.py` uses a fake IC transport around the real primitive predicate and is not a genuine runtime IC-to-IC proof.

## GenLayer Direct Mode suite

`tests/test_direct_mode.py` uses `genlayer-test==0.29.2`, `direct_deploy`, `direct_vm`, `mock_web`, `mock_llm`, `expect_revert`, `run_validator`, and `check_pickling` to verify core runtime behavior. These tests require GenLayer's downloaded GenVM artifacts and can only count as passing once actually executed. Do not confuse a simulated LLM answer with live validator agreement. On this Windows host, all five Direct Mode cases currently fail in `gltest.direct.loader._inject_message_to_fd0` before contract loading: Windows refuses to unlink the temporary message file while it is still attached to stdin. This is a test-runtime/platform failure, not evidence that the scenarios passed. The pinned CI workflow runs on Ubuntu, but its result must be checked after a push.

## Local handoff run

Verified with Python 3.12.10, pytest 9.0.2, GenLayer Test 0.29.2, GenVM Linter 0.11.0, repository-local GenLayer CLI 0.39.1, and `GENVM_VERSION=v0.2.12`:

- Deterministic primitive and consumer tests: **40 passed**.
- Linter `lint`, `validate`, `check`, strict `typecheck`, and `schema`: run for both contracts against the pinned v0.2.12 bundle. Lint and SDK validation passed; typecheck reported 0 errors and 0 warnings; schemas were emitted.
- Preflight and compileall: passed.
- `npm ci`: installed from the generated lockfile using lifecycle scripts disabled after the default Windows install hit a package-fetch permission error. The CLI version and StudioNet network guard were verified using the local package.
- StudioNet guard: verified chain 61999 at the exact configured RPC.
- Direct Mode: **5 failed before contract loading** due to the Windows temp-file unlink issue described above.
- GitHub Actions and live contract lifecycle: not yet run. The target GitHub repository is empty, but the saved GitHub credentials are invalid; no CLI wallet is available for deployment.

## StudioNet real lifecycle evidence

No deployment address, transaction hash, finalized receipt, or proof that external GitHub URLs were fetched by independent live validators is available in this checkout. The source folder is not a Git repository, GitHub access failed, and no CLI wallet evidence was supplied. Full network finality must be established on **StudioNet chain ID 61999** against `https://studio.genlayer.com/api`, with a local `genlayer@0.39.1` CLI. Evidence must distinguish leader execution, validator consensus, finality, actual on-chain state, and a second consumer transaction. These observations belong to real deployment records, not a synthetic test result.

## Negative tests that particularly matter

1. A proposal appears COVERED but inserts a password-only emergency bypass: classify material weakening, refuse ratification.
2. One dimension has only generic vendor claims but no operative evidence: GAP/UNKNOWN, refuse ratification.
3. Validator source SHA256 differs from the leader's: dissent / no consensus.
4. A valid passing evaluation is submitted by a non-owner: evaluation can be stored, but cannot become active without charter owner ratification.
5. A previously valid certificate is superseded: a consumer that pins the old hash must return false.
6. A new assessment is ratified after its maximum allowed 72h age: revert.
7. A pinned public source becomes unavailable: do not turn an assessment into an affirmative result.
8. A reviewer attempts to force approve from a model-provided confidence/score: model schema rejects extra fields and cannot influence the deterministic status.
