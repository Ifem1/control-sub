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
- Live StudioNet: ControlSub deployed at `0x9ce8C38E919F7BAD4E568aaC105eE05ed51Ac302` (transaction `0xcb6d7f569ea6ffdf6447ec1cf91cb7d81849ff3d92175f02a89805c2f63c95e5`, finalized with validator agreement). Charter `1` and candidate `1` were created by `0xD6423aE82a975d55C6CeaC222827A727325e0459`; proposal transaction `0xea60d4cea961d88f86d74df2430a7666bb79a8764777dafe1b70f7a7a4ba51e8` finalized with validator agreement.
- Three live `assess(1, candidate_hash)` submissions finalized as `MAJORITY_DISAGREE`: `0xfe0a57339e14d786f22fc76f30fbb10a879a4bd4b19544cad126d5c95803af6d`, `0xe19a868b95e8f5f86c11c7697460fa1821ee58c2702368fed99e9b17309894a4`, and `0x50547c1e8e2afb1d120f45e3acd93d5ba2b6f4d30d166439dfbd4f6451dc8994`. The candidate remains `SUBMITTED` (status 1) with no stored assessment or assessment hash. The latest leader output marked weakening `UNKNOWN` due to an unresolved dependency, so it was not ratified.
- No ratification or consumer deployment/execution was sent: the contract correctly blocks those steps without an agreed passing assessment. The test wallet balance before and after these transactions was `967.951289999999999986 GEN` (no observed balance change).

## StudioNet real lifecycle evidence

The primitive deployment, charter, proposal, and failed assessments above are live StudioNet observations. They do not prove a successful certificate or consumer execution. The source YAML remains illustrative and does not prove an operational gateway or review service. A passing consensus result and owner ratification are required before consumer deployment; neither is claimed here.

## Negative tests that particularly matter

1. A proposal appears COVERED but inserts a password-only emergency bypass: classify material weakening, refuse ratification.
2. One dimension has only generic vendor claims but no operative evidence: GAP/UNKNOWN, refuse ratification.
3. Validator source SHA256 differs from the leader's: dissent / no consensus.
4. A valid passing evaluation is submitted by a non-owner: evaluation can be stored, but cannot become active without charter owner ratification.
5. A previously valid certificate is superseded: a consumer that pins the old hash must return false.
6. A new assessment is ratified after its maximum allowed 72h age: revert.
7. A pinned public source becomes unavailable: do not turn an assessment into an affirmative result.
8. A reviewer attempts to force approve from a model-provided confidence/score: model schema rejects extra fields and cannot influence the deterministic status.
