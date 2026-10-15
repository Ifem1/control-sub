# Integration Contract

## Charter registration

`create_charter()` is a write by the initial owner. The returned integer and `get_charter(id)["charter_hash"]` are the immutable identity of the security rule. Bind the **exact charter hash** and ControlSub deployment address in every consumer; do not simply trust whichever charter a caller nominates.

`dimensions_json` must be a JSON list of 2–5 objects with exactly `id`, `objective`, `failure_mode`. All dimensions are mandatory. `allowed_repos_json` must be 1–4 lowercase `owner/repo` slugs. Evidence from other repos is not eligible.

## Candidate submission

`propose(charter_id, candidate_name, controls_json, expected_charter_hash)` may be called by anyone. Each alternative control is a bounded JSON object with exactly `id`, `mechanism`, `source_url`, `source_sha256`. The public source URL must be a `raw.githubusercontent.com` URL with exact 40-lowercase-hex commit hash. Compute the digest from **the exact published UTF-8 source bytes**, not from rendered HTML or downloaded markdown screenshots.

Submission alone does not certify anything. `get_candidate()` returns a deterministic `candidate_hash` which must be passed to `assess()`. Malformed models / unavailable sources can reject a transaction rather than store an assessment, and never open ratification.

## Assessment + ratification

`assess()` returns a status integer. Retrieve the candidate and its `assessment_hash`. Owner calls `ratify(candidate_id, assessment_hash, expected_current_certificate_hash)` only when status is 2 (`ASSESS_PASS`). For a charter with no active certificate, the expected current hash is `""`. To replace a current certificate, pass exactly the existing hash. Owner ratification is separate from validator consensus to avoid surprise policy changes.

`ratify()` returns the certificate hash. The old certificate becomes unusable immediately after ratification of its replacement. A charter owner can revoke its active certificate. A certificate naturally expires after the configured 1–90 days. Model verdicts are historical evidence; their presence does not imply a certificate is currently usable.

## Consumer rule

```python
@gl.contract_interface
class IControlSub:
    class View:
        def is_active(self, charter_id: u256, candidate_id: u256,
                      expected_certificate_hash: str, expected_charter_hash: str) -> bool: ...

sub = IControlSub(PINNED_CONTROLSUB_ADDRESS)
assert sub.view().is_active(PINNED_CHARTER_ID, candidate_id,
                            expected_certificate_hash, PINNED_CHARTER_HASH)
```

See `contracts/controlsub_consumer.py` for a deployable consumer that **also pins the action hash** and performs a one-shot action only if the substitution remains active. The action is intentionally a neutral boolean state transition: it demonstrates genuine composability without introducing escrow custody or an application.

## Security integration checklist

- Freeze deployment address + charter ID + charter hash at consumer creation, not per-call.
- Supply exact certificate hash, not just candidate ID or status 2.
- Re-check `is_active` in the *same write transaction* immediately before a protected operation.
- Treat return false as a hard denial. Do not fall back to off-chain LLM calls.
- Never treat a source-backed snapshot as proof a deployed configuration still matches it. Add independent operational controls for high-stakes consumers.
- Never rely on `get_candidate()["status"]` alone: a ratified certificate can be superseded, revoked or expired.
