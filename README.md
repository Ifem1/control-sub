# ControlSub

**An owner-ratified, consensus-grounded substitution primitive for security controls.**

A requirement often specifies a particular security mechanism even when another implementation may achieve the same security objectives. ControlSub permits a security charter owner to seal **atomic, explicit security objectives and failure modes**, invite alternative control bundles evidenced by immutable public files, obtain GenLayer leader/validator agreement on every dimension **plus absence of new material weakening**, and ratify a certificate that a separate Intelligent Contract can actually consume. No score-based LLM discretion can mint a certificate.

**Target:** GenLayer stable StudioNet • **chain ID 61999** • `https://studio.genlayer.com/api` • repository-local GenLayer CLI **0.39.1** • contract-only (no frontend, backend, database, Docker, or wallet-in-browser). The code targets the pinned `py-genlayer` runtime declared in each contract header. A second, minimal contract exists only to demonstrate integration.

## Core invariant

> A replacement is only actively certified if independent validators agree that **every mandatory frozen objective is documented as covered**, that **no new material weakening is established**, and if the charter's real owner separately ratifies it; a later expiry, revocation or supersession immediately invalidates downstream eligibility.

The outcome is not a legal compliance or real-world deployment guarantee. Public code/configuration proves what was **published at an exact GitHub commit**, not what a live server actually enforces. The registered owner authorizes the source repositories, not GenLayer. Consuming systems must choose realistic evidence criteria and make their own operational checks.

## Why GenLayer

Whether a hardware-key authentication gateway plus independent review has the same *security purpose* as an original two-person privileged-change control cannot be determined just by comparing vendor names, YAML keys, or numerical thresholds. The contract asks GenLayer validators to independently inspect the **same pinned published mechanisms** and classify complete coverage for each frozen security objective, including explicit failure modes, and identify hidden privilege expansion, bypasses or weakening. GenLayer consensus is restricted to that semantic relation. Input validation, provenance hashes, exact source IDs, status, owner authority, expiry, versioning and consumer permissions are all deterministic.

### Lifecycle

```text
create_charter(owner, baseline, 2..5 frozen dimensions, 1..4 trusted repos)
    |
    +-- exact public charter hash (cannot be edited or replaced)
    |
propose(permissionless alternative with 1..4 commit-pinned GitHub text sources)
    |
assess (leader fetch+hash+reason ; validators separately fetch+hash+reason)
    |                                 |
    |                                 +-- disagreement → no consensus / no state write
    |
    +-- ASSESS_FAIL / ASSESS_UNKNOWN → cannot ratify
    |
    +-- ASSESS_PASS
             |
      ratify(owner only, current-active-hash guard, ≤72h since assessment)
             |
      RATIFIED certificate, at most one active candidate per charter
             |
      consumer.view().is_active(...) → protected action
             |
      expiry / owner revoke / owner ratifies a new substitute
             |
      old certificate no longer active; history not deleted
```

## Security object and bounded outputs

A charter defines a baseline, context, owner-approved repository slugs and **2–5 mandatory atomic dimensions**. Each dimension is `{id, objective, failure_mode}`. The baseline, repository list and dimensions are sealed once at creation; no edit, upgrade, role-transfer, emergency bypass, or unguarded owner approval exists.

A candidate contains 1–4 `{id, mechanism, source_url, source_sha256}` controls. Sources must be public `raw.githubusercontent.com/owner/repo/<40 lowercase hex commit>/<path>` URLs and belong to the charter's allowlist. Files must be UTF-8 and 20–6000 bytes, with the submitted SHA256 of the exact returned bytes. Repositories are explicitly owner-approved; the contract does **not** claim those sources are independent of the proposer or prove they are deployed.

The model can only report a complete ordered decision vector:

```json
{
  "dimensions": [
    {"id": "STRONG_AUTH", "state": "COVERED", "supports": [0]},
    {"id": "DUAL_CONTROL", "state": "COVERED", "supports": [1]}
  ],
  "no_new_material_weakening": "YES",
  "reason_code": "ALL_COVERED"
}
```

`GAP`, `UNKNOWN`, `NO`, malformed fields, missing support indexes, unknown reasons or a dissenting substantive validator **never produce a passing certificate**. The result is derived deterministically as `ASSESS_PASS`, `ASSESS_FAIL`, or `ASSESS_UNKNOWN`. No LLM-created numerical score, self-reported confidence, or free-form rationale can override a missed mandatory objective.

## Exact interface

Writes:

```python
create_charter(title: str, context: str, baseline: str,
               dimensions_json: str, allowed_repos_json: str,
               certificate_lifetime_days: u32) -> u256

propose(charter_id: u256, name: str, controls_json: str,
        expected_charter_hash: str) -> u256

assess(candidate_id: u256, expected_candidate_hash: str) -> u8

ratify(candidate_id: u256, expected_assessment_hash: str,
       expected_current_certificate_hash: str) -> str

revoke(candidate_id: u256, expected_certificate_hash: str) -> bool

reject_pending(candidate_id: u256, expected_candidate_hash: str) -> bool
```

Views:

```python
get_charter(charter_id: u256) -> dict
get_candidate(candidate_id: u256) -> dict
get_certificate(candidate_id: u256) -> dict
is_active(charter_id: u256, candidate_id: u256,
          expected_certificate_hash: str,
          expected_charter_hash: str) -> bool
```

Status constants: `SUBMITTED=1`, `ASSESS_PASS=2`, `ASSESS_FAIL=3`, `ASSESS_UNKNOWN=4`, `RATIFIED=5`, `REVOKED=6`, `SUPERSEDED=7`, `OWNER_REJECTED=8`.

### Example

See [`examples/charter.json`](examples/charter.json) and [`examples/controls.template.json`](examples/controls.template.json). The control file contains immutable pins to the published example YAML at commit `4de8bac4e7cf68dc43c6d34bc3461157b6ad44be`; both raw GitHub URLs returned HTTP 200 and the exact Git blob bytes matched the recorded SHA256 digests. Verify future changes against the actual published bytes with `python scripts/check_source.py` before updating these pins.

Only an authorized repo is eligible; passing examples do not imply the YAML fixtures document production-grade controls. A proper live example should use nontrivial public, testable configuration plus meaningful negative controls.

## Local verification

```bash
python -m pytest tests/test_contract.py -q   # pure-Python deterministic mock suite
python scripts/preflight.py                 # static checks
python -m compileall -q contracts tests scripts
```

For *actual* GenLayer VM checking on a workstation with Python 3.12 and the required dependencies:

```bash
python -m pip install -r requirements-dev.txt -r requirements-lint.txt
genvm-lint check contracts/controlsub.py
genvm-lint check contracts/controlsub_consumer.py
python -m pytest tests/test_direct_mode.py -v
```

`tests/test_contract.py` uses a minimal deterministic SDK stub, not validator consensus. `tests/test_direct_mode.py` uses GenLayer's actual Direct Mode fixtures and source/LLM mocks. Neither is evidence of real multi-validator StudioNet finality. GitHub Actions runs both test layers when dependencies can be downloaded. No claim of live deployment is made by this repository.

The local GenLayer CLI is pinned in `package.json`; use the committed npm lockfile and `npm ci`. The deployment guard refuses any RPC whose chain ID is not **61999**, and refuses any CLI version other than **0.39.1**. Never point this project's scripts at 61997, Studio-dev or Studio-next. The deployment script guards immediately before the primitive deploy operation. Consumer deployment must be a separate guarded phase after the primitive address and pinned charter values have been independently verified; it is not safe to guess those runtime values or infer them from a deployment submission.

## Verification status

The source and evidence examples are published at [`Ifem1/control-sub`](https://github.com/Ifem1/control-sub). Commit `4de8bac4e7cf68dc43c6d34bc3461157b6ad44be` contains the pinned source files. The current `main` branch adds strict type fixes and CI updates; CI status is linked from the repository Actions page. The sample YAML demonstrates documented mechanisms only: it does not prove a production gateway or review service enforces them. No live ControlSub or consumer deployment address, transaction receipt, or completed on-chain lifecycle is claimed by this repository. See `docs/TEST_MATRIX.md` for the verification boundary.

## Composition

`contracts/controlsub_consumer.py` implements a typed view to the deployed primitive. It seals an exact charter hash, action hash and primitive address at construction; a protected action executes once, only when `ControlSub.is_active()` returns true for the expected candidate and certificate. A revoked, superseded, expired, wrong-charter or wrong-candidate receipt is not eligible. No dynamic contract calls are made from inside a nondeterministic block. See [`docs/INTEGRATION.md`](docs/INTEGRATION.md).

## Documentation

- [`docs/CONSENSUS.md`](docs/CONSENSUS.md) — validator protocol and decision invariants
- [`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md) — threat assumptions, attack cases and limitations
- [`docs/INTEGRATION.md`](docs/INTEGRATION.md) — charter and consumer API integration
- [`docs/TEST_MATRIX.md`](docs/TEST_MATRIX.md) — tests and verification boundaries

## References

- [GenLayer Equivalence Principle](https://docs.genlayer.com/developers/intelligent-contracts/equivalence-principle)
- [GenLayer Testing](https://docs.genlayer.com/developers/intelligent-contracts/testing)
- [GenLayer IC-to-IC calls](https://docs.genlayer.com/developers/intelligent-contracts/features/interacting-with-intelligent-contracts)

## License

MIT. See [`LICENSE`](LICENSE).
