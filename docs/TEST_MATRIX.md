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

## StudioNet negative-path audit

All transactions below were sent to StudioNet chain `61999` through `https://studio.genlayer.com/api` by the actual owner `0xD6423aE82a975d55C6CeaC222827A727325e0459`. Every call reached `FINALIZED`; consensus and GenVM execution results are recorded separately.

### Incorrect certificate

- Fresh consumer deployment `0xd14661f58528e8c5fb54d47d29c1312c8f815fb634dc3e2f92e4e998ee1530cf`: `FINALIZED`, `MAJORITY_AGREE`; the leader deployment receipt succeeded and the deployed contract was returned at `0x9eAc2aD543656D6E779264C0D56d6a2C2e229cbb`. It is pinned to charter `1`, the correct charter hash and the successful candidate's action hash.
- Execution `0x5b89e188369b6ae3ee2a890cd1c426e0bd66cd4ee47b45fed07cfa3eccd37b96`: `FINALIZED`, `MAJORITY_AGREE`; GenVM execution is `ERROR` with rollback payload `substitute not actively certified`. The submitted certificate was 64 zeroes instead of candidate `2`'s valid certificate.
- Independent `get_execution()` readback before and after is unchanged: `executed=false`, `candidate_id=0`, `certificate_hash=""`, charter `1`, expected charter/action hashes and the owner address. This is an agreed execution rejection, not just a failed validator vote.

### Incorrect candidate binding

- Fresh consumer deployment `0x5e1284978962d0734cd1381f2b0d3195ab0a20f817dcba4b8c4fbf55ff77184f`: `FINALIZED`, `MAJORITY_AGREE`, GenVM deployment execution `SUCCESS`; deployed at `0xE6a77779230fbC3f3837Ad41E1899eF29b3790F0`, pinned to the correct charter `1` and action hash.
- Execution `0xa20fec6fc4e2b7128d41f8a1e68ae43052fac21aaaf5b51d9cb8864cd9065dde`: `FINALIZED`, `MAJORITY_AGREE`; GenVM execution is `ERROR` with rollback payload `substitute not actively certified`. It supplied the valid candidate `2` certificate with candidate ID `1`, which is not ratified.
- Independent before/after readback is unchanged: `executed=false`, `candidate_id=0`, and `certificate_hash=""`; the charter and action pins remain as deployed.

### Isolated revocation proof blocked by validator disagreement

- The real owner created isolated charter `2` in transaction `0x93becf0811b74de0ccb30d006816d3451d50710be2c781ae198776387ff63800` (`FINALIZED`, `MAJORITY_AGREE`, leader execution `SUCCESS`, return value `2`). Readback: owner `0xD6423aE82a975d55C6CeaC222827A727325e0459`, charter hash `c06e1ce1107c5119cf173e6f3ee14e62ebf2067a59db11db0c51f589b6110484`.
- Candidate `3` was proposed in `0xf4760b26507a51f1766026fea2114b08727b55c115e899b130ef567598d5c265` (`FINALIZED`, `MAJORITY_AGREE`, leader execution `SUCCESS`, return value `3`).
- Assessment `0x4a070f8271e3b50130f91cee609135e726bbc11c0b7d22da15f6193be70cb191` finalized as `MAJORITY_DISAGREE`; the leader execution returned status `2`, while three validator votes were `DISAGREE` and two were `IDLE`. Because the transaction did not reach agreement, no assessment was stored.
- One retry, `0xa99f7d42cead173ee9defa5a77dd9fd04a742713c8354badcb898dd2aa92681e`, also finalized `MAJORITY_DISAGREE`; the leader execution returned status `2`, while three validator votes were `DISAGREE` and two were `IDLE`. The on-chain readback remains candidate `3`, status `SUBMITTED` (`1`), `assessment=null`, empty assessment hash, certificate inactive, and `is_active(2,3,...)=false`.
- No ratification, revocation, or consumer call followed: without an agreed passing assessment there was no valid certificate to revoke. The successful charter `1` / candidate `2` remains `RATIFIED` and active, and its original consumer remains executed. The disagreement is preserved as the actual consensus blocker; it is not described as a completed revocation denial.

The two consumer rollback transactions demonstrate certificate and candidate guards. The revocation scenario remains unproven because StudioNet validators disagreed twice on the isolated candidate. The original successful positive lifecycle and its historical receipts remain intact.

## Negative tests that particularly matter

1. A proposal appears COVERED but inserts a password-only emergency bypass: classify material weakening, refuse ratification.
2. One dimension has only generic vendor claims but no operative evidence: GAP/UNKNOWN, refuse ratification.
3. Validator source SHA256 differs from the leader's: dissent / no consensus.
4. A valid passing evaluation is submitted by a non-owner: evaluation can be stored, but cannot become active without charter owner ratification.
5. A previously valid certificate is superseded: a consumer that pins the old hash must return false.
6. A new assessment is ratified after its maximum allowed 72h age: revert.
7. A pinned public source becomes unavailable: do not turn an assessment into an affirmative result.
8. A reviewer attempts to force approve from a model-provided confidence/score: model schema rejects extra fields and cannot influence the deterministic status.
