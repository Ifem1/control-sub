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
- Evidence sources: executable reference controls and behavior checks are published at commit `93cdba4efef619202f00a50783f866b7e5c8f60b`; their exact source SHA256 digests are pinned in the candidate controls. These demonstrate the reference code behavior only and do not establish that a production identity or deployment service uses the code.
- Live StudioNet: ControlSub deployed at `0x9ce8C38E919F7BAD4E568aaC105eE05ed51Ac302` (transaction `0xcb6d7f569ea6ffdf6447ec1cf91cb7d81849ff3d92175f02a89805c2f63c95e5`, finalized with validator agreement). Charter `1` and candidate `1` were created by `0xD6423aE82a975d55C6CeaC222827A727325e0459`; proposal transaction `0xea60d4cea961d88f86d74df2430a7666bb79a8764777dafe1b70f7a7a4ba51e8` finalized with validator agreement.
- The first sample candidate's three assessments finalized `MAJORITY_DISAGREE`: `0xfe0a57339e14d786f22fc76f30fbb10a879a4bd4b19544cad126d5c95803af6d`, `0xe19a868b95e8f5f86c11c7697460fa1821ee58c2702368fed99e9b17309894a4`, and `0x50547c1e8e2afb1d120f45e3acd93d5ba2b6f4d30d166439dfbd4f6451dc8994`. Candidate `1` remained unratified. No actions were taken on that candidate.
- Follow-up candidate `2` used the executable reference-control evidence. Proposal `0x859fc1b0e7765de7a0023009012b2c36e95e81641af0f0e0be1bda49a4c0c688` and assessment `0xceb68ba07cacdd101948e32d68740edd872ba890a1c0e5ed1834e516d48d27d8` finalized `MAJORITY_AGREE`; assessment status passed. Owner ratification `0xcb02876325e59afcdc10bbe651b457bed1e95aef303cd3ba95a0462dd7101d2f` finalized `MAJORITY_AGREE` with certificate hash `43ff9e900eb6815c246e0ecba84040c3e860c3555608ab816265a18936663679`.
- Consumer deployed at `0xdfEB10D80179FD2D9cFc8d7590Bcb29657bBE300` (deployment transaction `0x67b9601312091c3b2d8df82f29703e51107f4013c196932ec7d62298296fcfcc`). Guarded one-shot action `0xf51ed84b037a78c3ae49a6f6e6b75a7cabb1f2a277cc7ae21a4ca9a66f6542c6` finalized `MAJORITY_AGREE`; on-chain readback confirms `executed: true`, candidate `2`, charter `1`, owner `0xD6423aE82a975d55C6CeaC222827A727325e0459`, the expected certificate and action hashes. Wallet balance remained `967.951289999999999986 GEN` before and after the full cycle.

## StudioNet real lifecycle evidence

The primitive deployment, failed initial sample assessment, passing follow-up assessment, owner ratification, consumer deployment and guarded execution above are live StudioNet observations. The executable reference code is evidence of its own behavior; it does not prove a production gateway or review service uses it. The successful cycle proves that the contract's certificate and consumer gates completed on StudioNet for this demo proposal.

## Negative tests that particularly matter

1. A proposal appears COVERED but inserts a password-only emergency bypass: classify material weakening, refuse ratification.
2. One dimension has only generic vendor claims but no operative evidence: GAP/UNKNOWN, refuse ratification.
3. Validator source SHA256 differs from the leader's: dissent / no consensus.
4. A valid passing evaluation is submitted by a non-owner: evaluation can be stored, but cannot become active without charter owner ratification.
5. A previously valid certificate is superseded: a consumer that pins the old hash must return false.
6. A new assessment is ratified after its maximum allowed 72h age: revert.
7. A pinned public source becomes unavailable: do not turn an assessment into an affirmative result.
8. A reviewer attempts to force approve from a model-provided confidence/score: model schema rejects extra fields and cannot influence the deterministic status.
