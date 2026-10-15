# Verification Matrix

## Offline mocked SDK suite

`tests/test_contract.py` executes the actual Python contract against a minimal test double. It does **not** execute GenVM nor prove real consensus. It covers complete pass, missing dimension, unknown dimension, forged leader, new weakening, source digest mismatch, unavailable/oversize sources, non-allowlisted/moving Git URLs, duplicate source inflation, typoed objective IDs, duplicate IDs, unsupported/unordered/repeated evidence indexes, malformed verdicts, owner-only ratification, stale hashes, stale ratification, replay assessment, supersession, time expiry, revocation, owner rejection, and consumer predicate false on unknown IDs. `tests/test_consumer.py` uses a fake IC transport around the real primitive predicate and is not a genuine runtime IC-to-IC proof.

## GenLayer Direct Mode suite

`tests/test_direct_mode.py` uses `genlayer-test==0.29.2`, `direct_deploy`, `direct_vm`, `mock_web`, `mock_llm`, `expect_revert`, `run_validator`, and `check_pickling` to exercise actual GenVM Direct Mode. It does not prove public-network multi-validator consensus because the web and LLM inputs are mocked. The full suite and all five Direct Mode tests passed in GitHub Actions on Ubuntu in [run 38787005748](https://github.com/Ifem1/control-sub/actions/runs/38787005748). On this Windows workstation, Direct Mode cannot start: `gltest.direct.loader._inject_message_to_fd0` attempts to unlink a temporary message file still attached to stdin, which Windows refuses. This platform issue does not affect the Ubuntu CI execution.

## Local handoff run

Verified with Python 3.12.10, pytest 9.0.2, GenLayer Test 0.29.2, GenVM Linter 0.11.0, repository-local GenLayer CLI 0.39.1, and `GENVM_VERSION=v0.2.12`:

- Deterministic primitive and consumer tests: **40 passed**.
- Linter `lint`, `validate`, `check`, strict `typecheck`, and `schema`: run for both contracts against the pinned v0.2.12 bundle. Lint and SDK validation passed; typecheck reported 0 errors and 0 warnings; schemas were emitted.
- Preflight and compileall: passed.
- `npm ci`: installed from the generated lockfile using lifecycle scripts disabled after the default Windows install hit a package-fetch permission error. The CLI version and StudioNet network guard were verified using the local package.
- StudioNet guard: verified chain 61999 at the exact configured RPC.
- Direct Mode: **5 passed in GitHub Actions on Ubuntu**; local Windows execution remains blocked before contract loading by the temp-file unlink issue described above.
- GitHub Actions: **passed** in [run 38787005748](https://github.com/Ifem1/control-sub/actions/runs/38787005748), including npm ci, CLI version/network guard, all linter checks, strict typechecks, schema extraction, full pytest, Direct Mode, preflight, and compileall.
- Evidence sources: `examples/gateway.yml` and `examples/review.yml` are publicly retrievable at commit `4de8bac4e7cf68dc43c6d34bc3461157b6ad44be`; published raw URLs returned HTTP 200 and their Git blob SHA256 digests are pinned in `examples/controls.template.json`.
- Live StudioNet lifecycle: not run. The configured CLI has an active funded account, but it is locked; its unlock credential is not available in this session. No contract addresses, transaction receipts, or on-chain success claims are recorded.

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
